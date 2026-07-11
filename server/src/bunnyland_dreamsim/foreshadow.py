"""Recurring nightmares foreshadow storyteller pressure (core storyteller integration).

A recurring nightmare is a warning. When the core **storyteller** is running, dreamsim folds
a little extra *threat* into its incident budget, so a sleeper's dread quietly pulls a coming
incident nearer — an omen that pays off in the waking world.

The storyteller is a core mechanic, so its component types are imported directly. Dreamsim
still runs standalone: if no storyteller entity exists in the world the nudge is a no-op, a
warning is logged (the synergy is simply off), and the omen stays purely narrative.
"""

from __future__ import annotations

import logging
from dataclasses import replace

from bunnyland.core.ecs import replace_component
from bunnyland.foundation.storyteller.mechanics import StorytellerComponent, ThreatPointsComponent
from relics import World

LOG = logging.getLogger(__name__)

#: Threat points a single recurring nightmare adds to a storyteller's incident budget.
FORESHADOW_THREAT_POINTS = 3.0


def foreshadow_storyteller(world: World, points: float = FORESHADOW_THREAT_POINTS) -> bool:
    """Nudge every running storyteller's threat budget upward; return whether any was nudged.

    Returns ``False`` (and logs a warning that the synergy is off) when the world has no
    storyteller entity, leaving the dream's omen as narrative-only.
    """
    nudged = False
    for entity in world.query().with_all([StorytellerComponent]).execute_entities():
        current = (
            entity.get_component(ThreatPointsComponent)
            if entity.has_component(ThreatPointsComponent)
            else ThreatPointsComponent()
        )
        replace_component(entity, replace(current, points=current.points + points))
        nudged = True
    if not nudged:
        LOG.warning(
            "recurring nightmare could not foreshadow: no storyteller in the world; "
            "dream-omen foreshadowing is disabled"
        )
    return nudged


__all__ = ["FORESHADOW_THREAT_POINTS", "foreshadow_storyteller"]
