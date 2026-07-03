"""The rest-quality consequence: grade each sleeper's rest from bed + room safety.

Registered per-tick alongside the dream consequence. For every sleeping character it derives
a :class:`RestQualityComponent` from the comfort of the best bed in their room and how safe
that room is. Better rest yields a higher ``recovery`` multiplier other systems can read.
"""

from __future__ import annotations

from dataclasses import replace

from bunnyland.core import CharacterComponent, SleepingComponent
from bunnyland.core.ecs import replace_component
from bunnyland.core.events import DomainEvent
from relics import Entity, World

from .components import RestQualityComponent
from .conditions import SleepConditions, assess_sleep

#: Rest quality floor for a plain, safe sleep with no bed.
_BASE_QUALITY = 0.4

#: How much a fully comfortable bed can add to rest quality.
_BED_WEIGHT = 0.4

#: Penalty applied to a dangerous sleep.
_DANGER_PENALTY = 0.3

#: Bonus for a safe room (on top of any bed).
_SAFE_BONUS = 0.1


def rest_quality_for(conditions: SleepConditions) -> RestQualityComponent:
    """Pure derivation of rest quality from sleeping ``conditions`` (no ECS side effects)."""
    quality = _BASE_QUALITY + conditions.bed_comfort * _BED_WEIGHT
    if conditions.dangerous:
        quality -= _DANGER_PENALTY
    elif conditions.room_safe:
        quality += _SAFE_BONUS
    quality = round(min(1.0, max(0.0, quality)), 3)
    return RestQualityComponent(
        quality=quality,
        comfort=round(conditions.bed_comfort, 3),
        safe=not conditions.dangerous,
        recovery=quality,
    )


class RestQualityConsequence:
    """Keep each sleeping character's :class:`RestQualityComponent` in sync with their room."""

    def process(self, world: World, epoch: int) -> list[DomainEvent]:
        for character in list(world.query().with_all([SleepingComponent]).execute_entities()):
            if not character.has_component(CharacterComponent):
                continue
            self._grade(world, epoch, character)
        return []

    def _grade(self, world: World, epoch: int, character: Entity) -> None:
        conditions = assess_sleep(world, character)
        graded = replace(rest_quality_for(conditions), updated_at_epoch=epoch)
        if character.has_component(RestQualityComponent):
            current = character.get_component(RestQualityComponent)
            if replace(current, updated_at_epoch=epoch) == graded:
                return
        replace_component(character, graded)


__all__ = ["RestQualityConsequence", "rest_quality_for"]
