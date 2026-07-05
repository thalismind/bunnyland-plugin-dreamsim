"""Bunnyland plugin entrypoint for the out-of-tree dreamsim sleep & dreams pack."""

from __future__ import annotations

from bunnyland.plugins import (
    CommandContribution,
    ContentContribution,
    DependencyContribution,
    EcsContribution,
    Plugin,
    RuntimeContribution,
)

from .commands import RecallDreamsHandler, recall_dreams_action
from .components import BedComponent, DreamComponent, RestQualityComponent
from .events import (
    DreamComposedEvent,
    DreamOmenEvent,
    DreamsRecalledEvent,
    NightmareEvent,
    RecurringDreamEvent,
)
from .fragments import dreamsim_fragments
from .install import install_dreamsim
from .motifs import DreamsOf, MotifComponent

PLUGIN_ID = "bunnyland.dreamsim"


def plugin() -> Plugin:
    return Plugin(
        id=PLUGIN_ID,
        name="Bunnyland Dreamsim",
        version="0.2.0",
        default_enabled=True,
        # Optional synergy: when the specter pack is loaded, a frayed sleeper's dread
        # darkens their dreams. Consumed via a guarded import (see :mod:`.sanity`); dreamsim
        # still runs standalone, so this is a soft recommend, never a hard requirement.
        dependencies=DependencyContribution(recommends=("bunnyland.spectersim",)),
        ecs=EcsContribution(
            components=(
                DreamComponent,
                RestQualityComponent,
                BedComponent,
                MotifComponent,
            ),
            edges=(DreamsOf,),
        ),
        commands=CommandContribution(
            action_handlers=(RecallDreamsHandler,),
            action_definitions=(recall_dreams_action(),),
            typed_events=(
                DreamComposedEvent,
                NightmareEvent,
                RecurringDreamEvent,
                DreamOmenEvent,
                DreamsRecalledEvent,
            ),
        ),
        runtime=RuntimeContribution(service_factories=(install_dreamsim,)),
        content=ContentContribution(
            prompt_fragments=(dreamsim_fragments,),
        ),
    )


def bunnyland_plugins() -> list[Plugin]:
    return [plugin()]


__all__ = ["PLUGIN_ID", "bunnyland_plugins", "plugin"]
