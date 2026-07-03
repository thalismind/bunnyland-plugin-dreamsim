"""Domain events emitted while characters dream."""

from __future__ import annotations

from bunnyland.core.events import DomainEvent


class DreamComposedEvent(DomainEvent):
    """A sleeping character composed a new dream this tick."""

    character_id: str
    kind: str
    summary: str


class NightmareEvent(DomainEvent):
    """A sleeping character's dream turned into a nightmare (dangerous/unsafe sleep)."""

    character_id: str
    summary: str
    omen: str = ""


__all__ = ["DreamComposedEvent", "NightmareEvent"]
