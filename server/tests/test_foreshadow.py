from __future__ import annotations

from bunnyland.core import WorldActor, spawn_entity
from bunnyland.foundation.storyteller.mechanics import StorytellerComponent, ThreatPointsComponent

from bunnyland_dreamsim import FORESHADOW_THREAT_POINTS, foreshadow_storyteller


def test_no_storyteller_means_the_omen_is_narrative_only(caplog):
    actor = WorldActor()
    with caplog.at_level("WARNING"):
        nudged = foreshadow_storyteller(actor.world)
    assert nudged is False
    assert any("foreshadow" in rec.message for rec in caplog.records)


def test_a_running_storyteller_gains_threat_from_the_omen():
    actor = WorldActor()
    teller = spawn_entity(actor.world, [StorytellerComponent(), ThreatPointsComponent(points=2.0)])

    nudged = foreshadow_storyteller(actor.world)

    assert nudged is True
    assert teller.get_component(ThreatPointsComponent).points == 2.0 + FORESHADOW_THREAT_POINTS


def test_a_storyteller_without_threat_points_gets_them():
    actor = WorldActor()
    teller = spawn_entity(actor.world, [StorytellerComponent()])

    nudged = foreshadow_storyteller(actor.world, points=5.0)

    assert nudged is True
    assert teller.get_component(ThreatPointsComponent).points == 5.0
