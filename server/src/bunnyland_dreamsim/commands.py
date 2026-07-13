"""Player verb: ``recall-dreams`` — reflect on the dreams that keep returning to you.

A private, deterministic reflection with no side effects on the world. The acting character
reviews the dream **motifs** that recur for them (tracked as :class:`DreamsOf` edges) and, if
any has surfaced often enough to count as a *recurring* dream, surfaces them as a
:class:`DreamsRecalledEvent`. Dreams are private, so the verb only ever reflects on the
actor's own motifs. It rejects cleanly when the sleeper has nothing recurring yet.
"""

from __future__ import annotations

from bunnyland.core.actions import (
    ActionDefinition,
    ActionEffort,
    ActionExample,
    ActionRequirement,
    effort_cost,
)
from bunnyland.core.commands import Lane, SubmittedCommand
from bunnyland.core.events import event_base
from bunnyland.core.handlers import (
    HandlerContext,
    HandlerResult,
    planned,
    rejected,
    require_character,
)
from bunnyland.core.mutations import MutationPlan

from .events import DreamsRecalledEvent
from .motifs import recurring_motifs

#: Command type / verb name for recalling recurring dreams.
RECALL_DREAMS = "recall-dreams"


class RecallDreamsHandler:
    """Let a character deliberately recall the dreams that keep returning to them."""

    command_type = RECALL_DREAMS

    def execute(self, ctx: HandlerContext, command: SubmittedCommand) -> HandlerResult:
        actor_id, character, rejection = require_character(ctx, command.character_id)
        if rejection is not None:
            return rejection
        motifs = recurring_motifs(ctx.world, character)
        if not motifs:
            return rejected("you have no recurring dreams to recall")
        character_id = str(actor_id)
        return planned(
            MutationPlan(),
            DreamsRecalledEvent(
                **event_base(ctx.epoch, actor_id=character_id),
                character_id=character_id,
                subjects=tuple(motif.subject for motif in motifs),
                has_nightmare=any(motif.is_nightmare for motif in motifs),
            )
        )


def recall_dreams_action() -> ActionDefinition:
    """Client-neutral metadata for the ``recall-dreams`` verb."""
    return ActionDefinition(
        command_type=RECALL_DREAMS,
        title="Recall Dreams",
        description="Reflect on the dreams that keep returning to you.",
        icon="moon",
        lane=Lane.FOCUS,
        cost=effort_cost(focus=ActionEffort.ROUTINE),
        arguments={},
        examples=(ActionExample(text="recall-dreams"),),
        requirement=ActionRequirement(character_edges=("DreamsOf",)),
    )


__all__ = ["RECALL_DREAMS", "RecallDreamsHandler", "recall_dreams_action"]
