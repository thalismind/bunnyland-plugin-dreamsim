from __future__ import annotations

from bunnyland.core import IdentityComponent, WorldActor, spawn_entity

from bunnyland_dreamsim import (
    NIGHTMARE,
    PLEASANT,
    RECURRENCE_THRESHOLD,
    DreamsOf,
    MotifComponent,
    motif_key,
    recurring_motifs,
    reinforce_motif,
)


def _sleeper(world, name="Vin"):
    return spawn_entity(world, [IdentityComponent(name=name, kind="character")])


def test_motif_key_normalises_case_and_whitespace():
    assert motif_key("  The   Wraith ") == "the wraith"


def test_reinforcing_a_new_subject_spawns_a_motif_entity_and_edge():
    actor = WorldActor()
    sleeper = _sleeper(actor.world)

    result = reinforce_motif(actor.world, sleeper, "the wraith", NIGHTMARE, epoch=10)

    assert result.component.occurrences == 1
    assert result.component.first_epoch == 10
    assert result.component.is_nightmare
    assert result.entity.has_component(MotifComponent)
    edges = list(sleeper.get_relationships(DreamsOf))
    assert len(edges) == 1


def test_reinforcing_the_same_subject_reuses_and_strengthens_the_motif():
    actor = WorldActor()
    sleeper = _sleeper(actor.world)

    reinforce_motif(actor.world, sleeper, "the wraith", NIGHTMARE, epoch=10)
    result = reinforce_motif(actor.world, sleeper, "The Wraith", NIGHTMARE, epoch=20)

    assert result.component.occurrences == 2
    assert result.component.first_epoch == 10  # preserved
    assert result.component.last_epoch == 20
    # still exactly one motif entity for that subject
    assert len(list(sleeper.get_relationships(DreamsOf))) == 1


def test_a_motif_becomes_recurring_at_the_threshold():
    actor = WorldActor()
    sleeper = _sleeper(actor.world)

    result = None
    for epoch in range(RECURRENCE_THRESHOLD):
        result = reinforce_motif(actor.world, sleeper, "the meadow", PLEASANT, epoch=epoch)

    assert result.component.occurrences == RECURRENCE_THRESHOLD
    assert result.component.recurring


def test_recurring_motifs_lists_only_recurring_ones_strongest_first():
    actor = WorldActor()
    sleeper = _sleeper(actor.world)

    # "the wraith" recurs; "a fleeting thought" does not
    for epoch in range(RECURRENCE_THRESHOLD + 1):
        reinforce_motif(actor.world, sleeper, "the wraith", NIGHTMARE, epoch=epoch)
    reinforce_motif(actor.world, sleeper, "a fleeting thought", PLEASANT, epoch=99)

    motifs = recurring_motifs(actor.world, sleeper)
    assert [m.subject for m in motifs] == ["the wraith"]
    assert motifs[0].occurrences == RECURRENCE_THRESHOLD + 1


def test_recurring_motifs_sorted_by_occurrences_then_subject():
    actor = WorldActor()
    sleeper = _sleeper(actor.world)
    for _ in range(RECURRENCE_THRESHOLD):
        reinforce_motif(actor.world, sleeper, "beta", PLEASANT, epoch=1)
    for _ in range(RECURRENCE_THRESHOLD + 2):
        reinforce_motif(actor.world, sleeper, "alpha", PLEASANT, epoch=1)

    motifs = recurring_motifs(actor.world, sleeper)
    assert [m.subject for m in motifs] == ["alpha", "beta"]


def test_lookup_skips_dangling_and_non_motif_edges():
    actor = WorldActor()
    sleeper = _sleeper(actor.world)
    # an edge to a non-motif entity should be ignored by the lookup
    other = spawn_entity(actor.world, [IdentityComponent(name="rock", kind="thing")])
    sleeper.add_relationship(DreamsOf(), other.id)
    # a dangling edge to a removed entity should also be ignored
    ghost = spawn_entity(actor.world, [IdentityComponent(name="ghost", kind="thing")])
    sleeper.add_relationship(DreamsOf(), ghost.id)
    actor.world.remove(ghost.id)

    result = reinforce_motif(actor.world, sleeper, "the wraith", NIGHTMARE, epoch=1)
    assert result.component.occurrences == 1  # a fresh motif, not confused by the noise
    assert recurring_motifs(actor.world, sleeper) == []


def test_a_blank_subject_still_names_the_motif_entity():
    actor = WorldActor()
    sleeper = _sleeper(actor.world)
    result = reinforce_motif(actor.world, sleeper, "", PLEASANT, epoch=1)
    assert result.entity.get_component(IdentityComponent).name == "a half-formed motif"
