"""Bunnyland plugin entrypoint for the out-of-tree dreamsim sleep & dreams pack."""

from __future__ import annotations

from bunnyland.plugins import (
    CommandContribution,
    ContentContribution,
    EcsContribution,
    Plugin,
    RuntimeContribution,
)

from .components import BedComponent, DreamComponent, RestQualityComponent
from .events import DreamComposedEvent, NightmareEvent
from .fragments import dreamsim_fragments
from .install import install_dreamsim

PLUGIN_ID = "bunnyland_dreamsim"


def plugin() -> Plugin:
    return Plugin(
        id=PLUGIN_ID,
        name="Bunnyland Dreamsim",
        version="0.1.0",
        default_enabled=True,
        ecs=EcsContribution(
            components=(
                DreamComponent,
                RestQualityComponent,
                BedComponent,
            ),
        ),
        commands=CommandContribution(
            typed_events=(DreamComposedEvent, NightmareEvent),
        ),
        runtime=RuntimeContribution(service_factories=(install_dreamsim,)),
        content=ContentContribution(
            prompt_fragments=(dreamsim_fragments,),
        ),
    )


def bunnyland_plugins() -> list[Plugin]:
    return [plugin()]


__all__ = ["PLUGIN_ID", "bunnyland_plugins", "plugin"]
