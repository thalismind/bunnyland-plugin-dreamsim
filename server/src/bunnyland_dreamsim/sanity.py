"""Optional spectersim synergy: a frayed sleeper's dread darkens their dreams.

Dreamsim runs perfectly well standalone. When the specter pack happens to be installed, a
sleeper whose **sanity** has frayed carries that dread into the night: even a safe, quiet
room breeds a themed nightmare. When the pack is not installed the guarded import simply
fails, a warning is logged (the synergy is off), and sleepers dream only from their room,
memories, and mood — still fully deterministic and offline.

The guarded import is the only place dreamsim ever touches the specter pack, and we read a
value (the dread band) rather than reaching into its state.
"""

from __future__ import annotations

import logging

from relics import Entity

logger = logging.getLogger(__name__)

try:  # Soft, optional: the specter pack may not be installed.
    from bunnyland_spectersim.sanity import STABLE as _STABLE
    from bunnyland_spectersim.sanity import SanityComponent as _SanityComponent
    from bunnyland_spectersim.sanity import sanity_band as _sanity_band
except ImportError:  # Standalone: no specter pack, so sanity never colours a dream.
    _SanityComponent = None
    _sanity_band = None
    _STABLE = "stable"
    logger.warning(
        "bunnyland_spectersim not installed; dreamsim reads no sanity dread into dreams."
    )

#: The nightmare subject a frayed sleeper fixates on when the specter pack is present.
DREAD_SUBJECT = "the thing gnawing at the edge of your mind"


def dread_subject(character: Entity) -> str:
    """A themed nightmare subject when the sleeper's sanity has frayed; ``""`` otherwise.

    Returns an empty string when the specter pack is absent, the character carries no sanity
    component, or their sanity is still ``stable`` — in every one of those cases the night is
    left to form from the room, memories, and mood alone.
    """
    if _SanityComponent is None or not character.has_component(_SanityComponent):
        return ""
    band = _sanity_band(character.get_component(_SanityComponent))
    if band == _STABLE:
        return ""
    return DREAD_SUBJECT


__all__ = ["DREAD_SUBJECT", "dread_subject"]
