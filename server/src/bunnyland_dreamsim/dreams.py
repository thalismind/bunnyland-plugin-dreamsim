"""The dream consequence: compose a dream for each sleeping character, on a cadence.

Registered per-tick via :func:`bunnyland_dreamsim.install.install_dreamsim`. For every
character carrying the core :class:`SleepingComponent` it:

1. decides whether this sleep session is due for a (new) dream,
2. reads the sleeping conditions and the sleeper's recent private memories + mood,
3. composes a deterministic dream (:mod:`bunnyland_dreamsim.composer`),
4. writes a :class:`DreamComponent` onto the character and records the dream as a private
   memory (when a memory store is available), and
5. nudges mood — toward fear for nightmares, toward contentment for pleasant dreams — by
   dropping a decaying ``ThoughtComponent`` the core affect system folds into the mood.

It builds *on top of* the core sleep model; it never puts anyone to sleep or wakes them.
"""

from __future__ import annotations

from dataclasses import replace

from bunnyland.core import CharacterComponent, MemoryProfileComponent, SleepingComponent
from bunnyland.core.components import AffectComponent, AffectDelta, ThoughtComponent
from bunnyland.core.ecs import replace_component, spawn_entity
from bunnyland.core.edges import HasThought
from bunnyland.core.events import DomainEvent, event_base
from bunnyland.memory import MemoryEntry
from relics import Entity, World

from .components import PLEASANT, DreamComponent
from .composer import DreamHook, compose_dream
from .conditions import assess_sleep
from .connectors import cross_pack_signal
from .events import (
    DreamComposedEvent,
    DreamOmenEvent,
    NightmareEvent,
    RecurringDreamEvent,
)
from .foreshadow import foreshadow_storyteller
from .motifs import RECURRENCE_THRESHOLD, reinforce_motif
from .sanity import dread_subject

#: A character must be asleep at least this many epochs before their first dream forms.
DREAM_ONSET = 300

#: Once a dream has formed, wait at least this many epochs before composing the next one.
DREAM_INTERVAL = 1800

#: How many recent memories to weave a dream from.
MEMORY_SAMPLE = 5

#: How long a dream-born thought lingers in the mood system (game seconds).
DREAM_THOUGHT_TTL = 4 * 3600

#: Mood shifts a dream drops as a thought.
_NIGHTMARE_DELTA = AffectDelta(fear=10.0, stress=8.0, valence=-5.0)
_PLEASANT_DELTA = AffectDelta(valence=6.0, stress=-4.0)


class DreamConsequence:
    """Compose and record a deterministic dream for each sleeping character."""

    def __init__(
        self,
        *,
        store=None,
        onset: int = DREAM_ONSET,
        interval: int = DREAM_INTERVAL,
        hook: DreamHook | None = None,
    ) -> None:
        self.store = store
        self.onset = onset
        self.interval = interval
        self.hook = hook

    def process(self, world: World, epoch: int) -> list[DomainEvent]:
        events: list[DomainEvent] = []
        for character in list(world.query().with_all([SleepingComponent]).execute_entities()):
            if not character.has_component(CharacterComponent):
                continue
            if self._should_dream(character, epoch):
                events.extend(self._dream(world, epoch, character))
        return events

    def _should_dream(self, character: Entity, epoch: int) -> bool:
        sleeping = character.get_component(SleepingComponent)
        if epoch - sleeping.started_at_epoch < self.onset:
            return False
        if not character.has_component(DreamComponent):
            return True
        dream = character.get_component(DreamComponent)
        if dream.sleep_started != sleeping.started_at_epoch:
            return True  # a new sleep session — dream afresh
        return (epoch - dream.created_at_epoch) >= self.interval

    def _dream(self, world: World, epoch: int, character: Entity) -> list[DomainEvent]:
        sleeping = character.get_component(SleepingComponent)
        conditions = assess_sleep(world, character)
        collection = self._collection(character)
        entries = self._recent_entries(collection)
        memories = [entry.text for entry in entries][:MEMORY_SAMPLE]
        signal = self._signal(character, entries)
        affect = (
            character.get_component(AffectComponent).current
            if character.has_component(AffectComponent)
            else None
        )
        seed_key = f"{character.id}:{sleeping.started_at_epoch}:{epoch}"
        draft = compose_dream(conditions, memories, affect, seed_key, hook=self.hook, signal=signal)

        replace_component(
            character,
            DreamComponent(
                summary=draft.summary,
                text=draft.text,
                kind=draft.kind,
                quality=draft.quality,
                based_on_memory=draft.based_on_memory,
                omen=draft.omen,
                sleep_started=sleeping.started_at_epoch,
                created_at_epoch=epoch,
            ),
        )
        self._record_memory(collection, draft.text, draft.kind, epoch)
        self._shift_mood(world, epoch, character, draft.kind)

        character_id = str(character.id)
        events: list[DomainEvent] = [
            DreamComposedEvent(
                **event_base(epoch, actor_id=character_id),
                character_id=character_id,
                kind=draft.kind,
                summary=draft.summary,
            )
        ]
        if draft.kind != PLEASANT:
            events.append(
                NightmareEvent(
                    **event_base(epoch, actor_id=character_id),
                    character_id=character_id,
                    summary=draft.summary,
                    omen=draft.omen,
                )
            )
        events.extend(self._reinforce(world, epoch, character, draft.summary, draft.kind))
        return events

    def _signal(self, character: Entity, entries: list[MemoryEntry]):
        """Fold cross-pack memory tone and (optionally) specter dread into one tone hint."""
        signal = cross_pack_signal(entries)
        if not signal.dread_subject:
            dread = dread_subject(character)
            if dread:
                signal = replace(signal, dread_subject=dread)
        return signal

    def _reinforce(
        self, world: World, epoch: int, character: Entity, subject: str, kind: str
    ) -> list[DomainEvent]:
        """Strengthen the dream's motif and emit recurring-dream / omen events as it grows.

        A motif that has just crossed the recurrence threshold announces itself with a
        :class:`RecurringDreamEvent`; a *recurring nightmare* additionally foreshadows
        storyteller pressure every night it returns, emitting a :class:`DreamOmenEvent`.
        """
        motif = reinforce_motif(world, character, subject, kind, epoch).component
        character_id = str(character.id)
        events: list[DomainEvent] = []
        if motif.occurrences == RECURRENCE_THRESHOLD:
            events.append(
                RecurringDreamEvent(
                    **event_base(epoch, actor_id=character_id),
                    character_id=character_id,
                    kind=motif.kind,
                    subject=motif.subject,
                    occurrences=motif.occurrences,
                )
            )
        if motif.recurring and motif.is_nightmare:
            foreshadows = foreshadow_storyteller(world)
            events.append(
                DreamOmenEvent(
                    **event_base(epoch, actor_id=character_id),
                    character_id=character_id,
                    subject=motif.subject,
                    occurrences=motif.occurrences,
                    foreshadows=foreshadows,
                )
            )
        return events

    def _collection(self, character: Entity) -> str | None:
        if self.store is None or not character.has_component(MemoryProfileComponent):
            return None
        return character.get_component(MemoryProfileComponent).vector_collection

    def _recent_entries(self, collection: str | None) -> list[MemoryEntry]:
        if self.store is None or collection is None:
            return []
        entries = self.store.search(collection, mode="recent", limit=MEMORY_SAMPLE + 5)
        # Exclude the plugin's own dream notes so dreams do not feed on themselves.
        return [entry for entry in entries if entry.source != "dream"]

    def _record_memory(self, collection: str | None, text: str, kind: str, epoch: int) -> None:
        if self.store is None or collection is None or not text:
            return
        self.store.add(
            collection,
            text=text,
            tags=("dream", kind),
            created_at_epoch=epoch,
            source="dream",
        )

    def _shift_mood(self, world: World, epoch: int, character: Entity, kind: str) -> None:
        if not character.has_component(AffectComponent):
            return
        if kind == PLEASANT:
            label, text, delta = "rested", "A good dream.", _PLEASANT_DELTA
        else:
            label, text, delta = "shaken", "A bad dream clings.", _NIGHTMARE_DELTA
        thought = spawn_entity(
            world,
            [
                ThoughtComponent(
                    label=label,
                    text=text,
                    affect_delta=delta,
                    created_at_epoch=epoch,
                    expires_at_epoch=epoch + DREAM_THOUGHT_TTL,
                )
            ],
        )
        character.add_relationship(HasThought(), thought.id)


__all__ = [
    "DREAM_INTERVAL",
    "DREAM_ONSET",
    "DREAM_THOUGHT_TTL",
    "MEMORY_SAMPLE",
    "DreamConsequence",
]
