"""Read the sleeping conditions around a character, deterministically.

Both the dream consequence and the rest-quality consequence need the same read of "how
safe and comfortable is this sleep?", so it lives here once. Everything is derived from
current ECS state — the room, its lighting, the entities sharing it, and any bed — so it is
stable given the same world.
"""

from __future__ import annotations

from dataclasses import dataclass

from bunnyland.core import (
    IdentityComponent,
    LightComponent,
    RoomComponent,
    container_of,
    contents,
)
from relics import Entity, World

from .components import BedComponent

#: Words that mark a co-present entity as a threat to sleep near.
HOSTILE_TERMS = (
    "hostile",
    "enemy",
    "monster",
    "monstrous",
    "ghost",
    "ghostly",
    "spirit",
    "specter",
    "spectre",
    "spectral",
    "wraith",
    "phantom",
    "haunt",
    "undead",
    "zombie",
    "demon",
    "predator",
    "threat",
    "aggressive",
    "beast",
    "kaiju",
)

#: Below this light level a room counts as dark (you cannot see a threat coming).
DARK_LEVEL = 0.2


@dataclass(frozen=True)
class SleepConditions:
    """A deterministic snapshot of one character's sleeping conditions."""

    room_title: str = "the open"
    room_safe: bool = True
    dark: bool = False
    threat: str = ""
    bed_comfort: float = 0.0

    @property
    def has_threat(self) -> bool:
        return bool(self.threat)

    @property
    def dangerous(self) -> bool:
        """Whether this sleep should breed nightmares and omens rather than pleasant dreams."""
        return self.has_threat or not self.room_safe or self.dark

    @property
    def comfortable(self) -> bool:
        """Whether this sleep is safe *and* has a decent bed — the recipe for a good dream."""
        return not self.dangerous and self.bed_comfort > 0.0


def _is_hostile(identity: IdentityComponent) -> bool:
    text = " ".join((identity.name, identity.kind, *identity.tags)).casefold()
    return any(term in text for term in HOSTILE_TERMS)


def assess_sleep(world: World, character: Entity) -> SleepConditions:
    """Read the room around ``character`` into a :class:`SleepConditions`.

    A sleeper with no room (uncontained) is treated as sleeping in the open: not indoors,
    no bed, but not actively threatened.
    """
    room_id = container_of(character)
    if room_id is None or not world.has_entity(room_id):
        return SleepConditions()
    room = world.get_entity(room_id)
    room_component = (
        room.get_component(RoomComponent) if room.has_component(RoomComponent) else None
    )
    room_title = room_component.title if room_component is not None else "the open"
    room_safe = room_component.safe if room_component is not None else True

    dark = False
    if room.has_component(LightComponent):
        light = room.get_component(LightComponent)
        dark = not light.enabled or light.level < DARK_LEVEL

    # Scan the room's other occupants for a threat and the best available bed. Sorting by id
    # keeps the "first" threat name stable regardless of contents() ordering.
    threat = ""
    bed_comfort = 0.0
    for other_id in sorted(contents(room), key=str):
        if other_id == character.id or not world.has_entity(other_id):
            continue
        other = world.get_entity(other_id)
        if other.has_component(BedComponent):
            bed_comfort = max(bed_comfort, other.get_component(BedComponent).comfort)
        if not threat and other.has_component(IdentityComponent):
            identity = other.get_component(IdentityComponent)
            if _is_hostile(identity):
                threat = identity.name or "something"

    return SleepConditions(
        room_title=room_title,
        room_safe=room_safe,
        dark=dark,
        threat=threat,
        bed_comfort=bed_comfort,
    )


__all__ = ["DARK_LEVEL", "HOSTILE_TERMS", "SleepConditions", "assess_sleep"]
