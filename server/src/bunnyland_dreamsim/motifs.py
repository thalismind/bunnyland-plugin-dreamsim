"""Recurring dream motifs, tracked as their own entities linked by a typed edge.

A **motif** is a subject a sleeper's dreams keep returning to — a lurking threat, a familiar
place, a remembered day. Rather than hang a growing *list* of motifs on the character (which
the engine cannot index), each motif is **its own entity** carrying a :class:`MotifComponent`
and linked from the dreamer by a :class:`DreamsOf` **typed edge**. One index per edge type
keeps a character's motifs queryable, and a single motif entity can strengthen night after
night until it becomes a *recurring* dream.

Everything here is deterministic: reinforcing a motif is pure ECS bookkeeping keyed on the
dream's condensed subject, with no randomness, clock, or model in the loop.
"""

from __future__ import annotations

from dataclasses import replace
from typing import NamedTuple

from bunnyland.core import IdentityComponent
from bunnyland.core.ecs import replace_component, spawn_entity
from pydantic.dataclasses import dataclass
from relics import Component, Edge, Entity, World

from .components import NIGHTMARE, PLEASANT

#: A motif becomes a *recurring* dream once its subject has surfaced this many times.
RECURRENCE_THRESHOLD = 3


@dataclass(frozen=True)
class MotifComponent(Component):
    """One recurring subject a dreamer keeps returning to, held on a motif entity."""

    subject: str = ""
    kind: str = PLEASANT
    occurrences: int = 0
    first_epoch: int = 0
    last_epoch: int = 0

    @property
    def is_nightmare(self) -> bool:
        return self.kind == NIGHTMARE

    @property
    def recurring(self) -> bool:
        """Whether this motif has surfaced often enough to count as a recurring dream."""
        return self.occurrences >= RECURRENCE_THRESHOLD


@dataclass(frozen=True)
class DreamsOf(Edge):
    """dreamer -> motif entity. Indexes the subjects a sleeper's dreams keep returning to."""


class MotifReinforcement(NamedTuple):
    """The result of reinforcing a motif: the motif entity and its fresh component value."""

    entity: Entity
    component: MotifComponent


def motif_key(subject: str) -> str:
    """A stable, whitespace/case-insensitive key so the same subject maps to one motif."""
    return " ".join(subject.split()).casefold()


def _find_motif(world: World, character: Entity, key: str) -> Entity | None:
    for _edge, motif_id in character.get_relationships(DreamsOf):
        if not world.has_entity(motif_id):
            continue
        motif = world.get_entity(motif_id)
        if not motif.has_component(MotifComponent):
            continue
        if motif_key(motif.get_component(MotifComponent).subject) == key:
            return motif
    return None


def reinforce_motif(
    world: World, character: Entity, subject: str, kind: str, epoch: int
) -> MotifReinforcement:
    """Record that ``character`` dreamt of ``subject`` again, strengthening its motif.

    Reuses the character's existing motif for that subject when one exists (bumping its
    occurrence count and latest tone), otherwise spawns a new motif entity and links it with
    a :class:`DreamsOf` edge.
    """
    key = motif_key(subject)
    existing = _find_motif(world, character, key)
    if existing is not None:
        current = existing.get_component(MotifComponent)
        updated = replace(
            current,
            kind=kind,
            occurrences=current.occurrences + 1,
            last_epoch=epoch,
        )
        replace_component(existing, updated)
        return MotifReinforcement(existing, updated)

    component = MotifComponent(
        subject=subject,
        kind=kind,
        occurrences=1,
        first_epoch=epoch,
        last_epoch=epoch,
    )
    motif = spawn_entity(
        world,
        [
            IdentityComponent(
                name=subject or "a half-formed motif",
                kind="motif",
                tags=("dreamsim", "motif"),
            ),
            component,
        ],
    )
    character.add_relationship(DreamsOf(), motif.id)
    return MotifReinforcement(motif, component)


def recurring_motifs(world: World, character: Entity) -> list[MotifComponent]:
    """The character's recurring motifs, strongest first (stable for prompts and tests)."""
    motifs: list[MotifComponent] = []
    for _edge, motif_id in character.get_relationships(DreamsOf):
        if not world.has_entity(motif_id):
            continue
        motif = world.get_entity(motif_id)
        if not motif.has_component(MotifComponent):
            continue
        component = motif.get_component(MotifComponent)
        if component.recurring:
            motifs.append(component)
    return sorted(motifs, key=lambda m: (-m.occurrences, m.subject))


__all__ = [
    "RECURRENCE_THRESHOLD",
    "DreamsOf",
    "MotifComponent",
    "MotifReinforcement",
    "motif_key",
    "recurring_motifs",
    "reinforce_motif",
]
