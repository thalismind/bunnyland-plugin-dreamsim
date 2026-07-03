"""Out-of-tree Bunnyland plugin: a sleep & dreams pack built on the core sleep model."""

from .components import (
    NIGHTMARE,
    PLEASANT,
    BedComponent,
    DreamComponent,
    RestQualityComponent,
)
from .composer import DreamDraft, DreamHook, compose_dream
from .conditions import SleepConditions, assess_sleep
from .dreams import DreamConsequence
from .events import DreamComposedEvent, NightmareEvent
from .fragments import dreamsim_fragments
from .install import install_dreamsim
from .plugin import PLUGIN_ID, bunnyland_plugins, plugin
from .prefabs import spawn_bed
from .rest import RestQualityConsequence, rest_quality_for

__all__ = [
    "NIGHTMARE",
    "PLEASANT",
    "PLUGIN_ID",
    "BedComponent",
    "DreamComponent",
    "DreamComposedEvent",
    "DreamConsequence",
    "DreamDraft",
    "DreamHook",
    "NightmareEvent",
    "RestQualityComponent",
    "RestQualityConsequence",
    "SleepConditions",
    "assess_sleep",
    "bunnyland_plugins",
    "compose_dream",
    "dreamsim_fragments",
    "install_dreamsim",
    "plugin",
    "rest_quality_for",
    "spawn_bed",
]
