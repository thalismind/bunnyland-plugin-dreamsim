"""Spawn factory for beds.

The loader does not consume ``ContentContribution.prefabs``, so a bed is created with this
``spawn_entity`` helper (from tests, admin tooling, or worldgen). A bed is a fixed furniture
item carrying a :class:`BedComponent`; pass ``room_id`` to place it in a room so anyone
sleeping there benefits from its comfort.
"""

from __future__ import annotations

from bunnyland.core import (
    ContainmentMode,
    Contains,
    IdentityComponent,
    spawn_entity,
)
from relics import Entity, World

from .components import BedComponent


def spawn_bed(
    world: World,
    *,
    room_id=None,
    comfort: float = 0.6,
    warmth: float = 0.5,
    name: str = "bed",
) -> Entity:
    """Spawn a bed, optionally placed in ``room_id``."""
    bed = spawn_entity(
        world,
        [
            IdentityComponent(name=name, kind="furniture", tags=("dreamsim", "bed")),
            BedComponent(comfort=comfort, warmth=warmth),
        ],
    )
    if room_id is not None and world.has_entity(room_id):
        world.get_entity(room_id).add_relationship(
            Contains(mode=ContainmentMode.ROOM_CONTENT), bed.id
        )
    return bed


__all__ = ["spawn_bed"]
