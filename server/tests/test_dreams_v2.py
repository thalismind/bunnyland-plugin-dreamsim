from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    MemoryProfileComponent,
    RoomComponent,
    SleepingComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.ecs import replace_component
from bunnyland.mechanics.storyteller import StorytellerComponent, ThreatPointsComponent
from bunnyland.memory import InMemoryStore

from bunnyland_dreamsim import (
    NIGHTMARE,
    PLEASANT,
    RECURRENCE_THRESHOLD,
    DreamComponent,
    DreamConsequence,
    recurring_motifs,
)
from bunnyland_dreamsim import sanity as sanity_module
from bunnyland_dreamsim.events import DreamOmenEvent, RecurringDreamEvent

COLLECTION = "vin-notes"


def _room(world, *, safe=True, title="Bedroom"):
    return spawn_entity(world, [RoomComponent(title=title, safe=safe)])


def _sleeper(world, room, *, name="Vin", started=0, profile=False):
    components = [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    if profile:
        components.append(MemoryProfileComponent(vector_collection=COLLECTION))
    character = spawn_entity(world, components)
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    replace_component(character, SleepingComponent(started_at_epoch=started))
    return character


def _threat(world, room, name="grendel"):
    enemy = spawn_entity(world, [IdentityComponent(name=name, kind="character", tags=("hostile",))])
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), enemy.id)
    return enemy


def _dream_until_recurring(actor):
    """Compose dreams tick by tick and return the events from the recurrence-crossing tick."""
    consequence = DreamConsequence(onset=0, interval=0)
    events = []
    for epoch in range(1, RECURRENCE_THRESHOLD + 1):
        events = consequence.process(actor.world, epoch)
    return events


# -- recurring dreams from a persistent threat -----------------------------------------


def test_a_persistent_threat_becomes_a_recurring_nightmare():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)
    _threat(actor.world, room)

    events = _dream_until_recurring(actor)

    recurring = [e for e in events if isinstance(e, RecurringDreamEvent)]
    assert len(recurring) == 1
    assert recurring[0].subject == "the grendel"
    assert recurring[0].kind == NIGHTMARE
    assert recurring[0].occurrences == RECURRENCE_THRESHOLD
    assert recurring_motifs(actor.world, sleeper)[0].subject == "the grendel"


def test_recurring_dream_event_fires_only_at_the_crossing():
    actor = WorldActor()
    room = _room(actor.world)
    _sleeper(actor.world, room)
    _threat(actor.world, room)
    consequence = DreamConsequence(onset=0, interval=0)

    # the first two nights are below threshold: no recurring event yet
    for epoch in (1, 2):
        events = consequence.process(actor.world, epoch)
        assert not any(isinstance(e, RecurringDreamEvent) for e in events)
    # a fourth night past the threshold does not re-announce recurrence
    consequence.process(actor.world, 3)
    fourth = consequence.process(actor.world, 4)
    assert not any(isinstance(e, RecurringDreamEvent) for e in fourth)


def test_a_recurring_nightmare_foreshadows_a_running_storyteller():
    actor = WorldActor()
    room = _room(actor.world)
    _sleeper(actor.world, room)
    _threat(actor.world, room)
    teller = spawn_entity(actor.world, [StorytellerComponent(), ThreatPointsComponent()])

    events = _dream_until_recurring(actor)

    omens = [e for e in events if isinstance(e, DreamOmenEvent)]
    assert len(omens) == 1
    assert omens[0].foreshadows is True
    assert teller.get_component(ThreatPointsComponent).points > 0.0


def test_a_recurring_nightmare_omen_without_a_storyteller_is_narrative_only():
    actor = WorldActor()
    room = _room(actor.world)
    _sleeper(actor.world, room)
    _threat(actor.world, room)

    events = _dream_until_recurring(actor)

    omens = [e for e in events if isinstance(e, DreamOmenEvent)]
    assert len(omens) == 1
    assert omens[0].foreshadows is False


def test_a_recurring_pleasant_dream_does_not_foreshadow():
    actor = WorldActor()
    room = _room(actor.world, title="Loft")
    _sleeper(actor.world, room)  # safe room, no threat -> pleasant, subject "the Loft"

    events = _dream_until_recurring(actor)

    assert any(isinstance(e, RecurringDreamEvent) for e in events)
    assert not any(isinstance(e, DreamOmenEvent) for e in events)


# -- cross-pack memory tone ------------------------------------------------------------


def test_a_remembered_fright_forces_a_nightmare_in_a_safe_room():
    actor = WorldActor()
    store = InMemoryStore()
    store.add(COLLECTION, text="a cryptid crossed the meadow", created_at_epoch=1)
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room, profile=True)

    DreamConsequence(store=store, onset=0).process(actor.world, 500)

    dream = sleeper.get_component(DreamComponent)
    assert dream.kind == NIGHTMARE
    assert "cryptid" in dream.summary


def test_a_remembered_celebration_sweetens_a_safe_night():
    actor = WorldActor()
    store = InMemoryStore()
    store.add(COLLECTION, text="the harvest festival lit the square", created_at_epoch=1)
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room, profile=True)

    DreamConsequence(store=store, onset=0).process(actor.world, 500)

    dream = sleeper.get_component(DreamComponent)
    assert dream.kind == PLEASANT
    assert "festival" in dream.summary


# -- spectersim sanity overlay ---------------------------------------------------------


def test_a_frayed_sleeper_dreams_a_nightmare_even_when_safe(monkeypatch):
    monkeypatch.setattr(sanity_module, "_SanityComponent", IdentityComponent)
    monkeypatch.setattr(sanity_module, "_sanity_band", lambda comp: "frayed")
    monkeypatch.setattr(sanity_module, "_STABLE", "stable")
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)  # safe room, no threat

    DreamConsequence(onset=0).process(actor.world, 500)

    assert sleeper.get_component(DreamComponent).kind == NIGHTMARE
