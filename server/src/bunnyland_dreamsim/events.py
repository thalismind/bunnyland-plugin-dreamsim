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


class RecurringDreamEvent(DomainEvent):
    """A dream motif has surfaced often enough to become a *recurring* dream."""

    character_id: str
    kind: str
    subject: str
    occurrences: int


class DreamOmenEvent(DomainEvent):
    """A recurring nightmare foreshadows coming pressure.

    ``foreshadows`` is ``True`` when a running storyteller was actually nudged (its incident
    budget gained a little threat); when no storyteller is present the omen is purely
    narrative and ``foreshadows`` is ``False``.
    """

    character_id: str
    subject: str
    occurrences: int
    foreshadows: bool = False


class DreamsRecalledEvent(DomainEvent):
    """A character deliberately recalled their recurring dreams (the ``recall-dreams`` verb)."""

    character_id: str
    subjects: tuple[str, ...]
    has_nightmare: bool = False


__all__ = [
    "DreamComposedEvent",
    "DreamOmenEvent",
    "DreamsRecalledEvent",
    "NightmareEvent",
    "RecurringDreamEvent",
]
