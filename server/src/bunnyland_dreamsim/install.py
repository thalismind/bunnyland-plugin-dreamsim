"""Runtime wiring: register the dream and rest-quality consequences on a world actor."""

from __future__ import annotations

from bunnyland.core.world_actor import WorldActor

from .dreams import DreamConsequence
from .rest import RestQualityConsequence


def install_dreamsim(actor: WorldActor) -> None:
    """Register the per-tick dream + rest consequences (a ``service_factories`` entry).

    If the core memory plugin has already installed a store on the actor, the dream
    consequence uses it to draw on (and record) the sleeper's private memories. Otherwise
    dreams are composed from mood and room alone — still fully deterministic and offline.
    """
    store = getattr(actor, "memory_store", None)
    actor.register_consequence(DreamConsequence(store=store))
    actor.register_consequence(RestQualityConsequence())


__all__ = ["install_dreamsim"]
