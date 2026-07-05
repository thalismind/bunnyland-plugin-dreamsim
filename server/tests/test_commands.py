from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    IdentityComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.commands import CommandCost, Lane, build_submitted_command
from bunnyland.core.handlers import HandlerContext

from bunnyland_dreamsim import (
    NIGHTMARE,
    PLEASANT,
    RECURRENCE_THRESHOLD,
    RecallDreamsHandler,
    reinforce_motif,
)
from bunnyland_dreamsim.commands import RECALL_DREAMS, recall_dreams_action
from bunnyland_dreamsim.events import DreamsRecalledEvent


def _character(world, name="Vin"):
    return spawn_entity(
        world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )


def _cmd(character_id):
    return build_submitted_command(
        character_id=str(character_id),
        controller_id="ctrl",
        controller_generation=0,
        command_type=RECALL_DREAMS,
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={},
    )


def _recur(world, character, subject, kind):
    for epoch in range(RECURRENCE_THRESHOLD):
        reinforce_motif(world, character, subject, kind, epoch=epoch)


def test_recall_surfaces_recurring_dreams():
    actor = WorldActor()
    character = _character(actor.world)
    _recur(actor.world, character, "the meadow", PLEASANT)

    ctx = HandlerContext(world=actor.world, epoch=100)
    result = RecallDreamsHandler().execute(ctx, _cmd(character.id))

    assert result.ok
    event = result.events[0]
    assert isinstance(event, DreamsRecalledEvent)
    assert event.subjects == ("the meadow",)
    assert event.has_nightmare is False


def test_recall_flags_a_recurring_nightmare():
    actor = WorldActor()
    character = _character(actor.world)
    _recur(actor.world, character, "the wraith", NIGHTMARE)

    ctx = HandlerContext(world=actor.world, epoch=100)
    result = RecallDreamsHandler().execute(ctx, _cmd(character.id))

    assert result.ok
    assert result.events[0].has_nightmare is True


def test_recall_rejects_when_nothing_recurs():
    actor = WorldActor()
    character = _character(actor.world)
    # a single dream is not yet recurring
    reinforce_motif(actor.world, character, "a passing thought", PLEASANT, epoch=1)

    ctx = HandlerContext(world=actor.world, epoch=100)
    result = RecallDreamsHandler().execute(ctx, _cmd(character.id))

    assert not result.ok
    assert result.reason == "you have no recurring dreams to recall"


def test_recall_rejects_an_invalid_character():
    actor = WorldActor()
    ctx = HandlerContext(world=actor.world, epoch=100)
    result = RecallDreamsHandler().execute(ctx, _cmd("not-an-id"))
    assert not result.ok


def test_recall_action_definition_is_registered_metadata():
    action = recall_dreams_action()
    assert action.command_type == RECALL_DREAMS
    assert action.lane == Lane.WORLD
    assert action.requirement.character_edges == ("DreamsOf",)
