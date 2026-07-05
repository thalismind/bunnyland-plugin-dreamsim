"""Out-of-tree Bunnyland plugin: a sleep & dreams pack built on the core sleep model."""

from .commands import RECALL_DREAMS, RecallDreamsHandler, recall_dreams_action
from .components import (
    NIGHTMARE,
    PLEASANT,
    BedComponent,
    DreamComponent,
    RestQualityComponent,
)
from .composer import DreamDraft, DreamHook, compose_dream
from .conditions import SleepConditions, assess_sleep
from .connectors import (
    DREAD_TERMS,
    SWEET_TERMS,
    CrossPackSignal,
    cross_pack_signal,
)
from .dreams import DreamConsequence
from .events import (
    DreamComposedEvent,
    DreamOmenEvent,
    DreamsRecalledEvent,
    NightmareEvent,
    RecurringDreamEvent,
)
from .foreshadow import FORESHADOW_THREAT_POINTS, foreshadow_storyteller
from .fragments import dreamsim_fragments
from .install import install_dreamsim
from .motifs import (
    RECURRENCE_THRESHOLD,
    DreamsOf,
    MotifComponent,
    MotifReinforcement,
    motif_key,
    recurring_motifs,
    reinforce_motif,
)
from .plugin import PLUGIN_ID, bunnyland_plugins, plugin
from .prefabs import spawn_bed
from .rest import RestQualityConsequence, rest_quality_for
from .sanity import dread_subject

__all__ = [
    "DREAD_TERMS",
    "FORESHADOW_THREAT_POINTS",
    "NIGHTMARE",
    "PLEASANT",
    "PLUGIN_ID",
    "RECALL_DREAMS",
    "RECURRENCE_THRESHOLD",
    "SWEET_TERMS",
    "BedComponent",
    "CrossPackSignal",
    "DreamComponent",
    "DreamComposedEvent",
    "DreamConsequence",
    "DreamDraft",
    "DreamHook",
    "DreamOmenEvent",
    "DreamsOf",
    "DreamsRecalledEvent",
    "MotifComponent",
    "MotifReinforcement",
    "NightmareEvent",
    "RecallDreamsHandler",
    "RecurringDreamEvent",
    "RestQualityComponent",
    "RestQualityConsequence",
    "SleepConditions",
    "assess_sleep",
    "bunnyland_plugins",
    "compose_dream",
    "cross_pack_signal",
    "dread_subject",
    "dreamsim_fragments",
    "foreshadow_storyteller",
    "install_dreamsim",
    "motif_key",
    "plugin",
    "recall_dreams_action",
    "recurring_motifs",
    "reinforce_motif",
    "rest_quality_for",
    "spawn_bed",
]
