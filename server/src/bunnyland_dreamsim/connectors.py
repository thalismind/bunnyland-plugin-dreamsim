"""Let other packs shape a dream through the shared MEMORY store — dependency-free.

dreamsim never imports another pack. Instead it reads the sleeper's own recent memories,
where other packs already record what happened to the character that day, and lets those
entries tilt the dream:

- a remembered **fright** — a cryptid sighting, a haunting, a bout of lost sanity — drags an
  otherwise-safe night into a themed nightmare (``dread_subject``);
- a remembered **celebration** — a festival, a feast — sweetens it (``sweet_subject``).

When no such memory is present the signal is empty and dreams form exactly as they do
standalone, so the pack has no hard dependency on any partner. Matching is deterministic:
a fixed set of terms checked against each entry's text, tags, and source.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from bunnyland.memory import MemoryEntry

#: Terms other packs' fright memories tend to carry (cryptid sightings, hauntings, sanity).
DREAD_TERMS = (
    "cryptid",
    "sighting",
    "haunt",
    "haunted",
    "haunting",
    "specter",
    "spectre",
    "spectral",
    "ghost",
    "wraith",
    "phantom",
    "sanity",
    "monster",
    "creature",
    "stalked",
    "lurking",
    "prowling",
    "howl",
    "dread",
)

#: Terms other packs' celebration memories tend to carry (festivals, feasts, gatherings).
SWEET_TERMS = (
    "festival",
    "feast",
    "celebration",
    "celebrated",
    "banquet",
    "party",
    "carnival",
    "fair",
    "parade",
    "dance",
    "wedding",
    "reunion",
    "homecoming",
)


@dataclass(frozen=True)
class CrossPackSignal:
    """A tone hint drawn from cross-pack memories: a fright and/or a celebration subject."""

    dread_subject: str = ""
    sweet_subject: str = ""

    @property
    def has_dread(self) -> bool:
        return bool(self.dread_subject)

    @property
    def has_sweet(self) -> bool:
        return bool(self.sweet_subject)


def _condense(text: str) -> str:
    """Condense a memory into a short dream-subject phrase (mirrors the dream composer)."""
    words = text.strip().split()
    if not words:
        return "something half-remembered"
    return " ".join(words[:6]).rstrip(".!,;:").lower()


def _haystack(entry: MemoryEntry) -> str:
    return " ".join((entry.text, entry.source, *entry.tags)).casefold()


def cross_pack_signal(entries: Sequence[MemoryEntry]) -> CrossPackSignal:
    """Read the freshest fright and celebration subjects out of ``entries`` (newest-first).

    Each direction latches onto the most recent matching memory, so the day's last scare or
    party is the one that colours the night. An empty sequence yields an empty signal.
    """
    dread = ""
    sweet = ""
    for entry in entries:
        haystack = _haystack(entry)
        if not dread and any(term in haystack for term in DREAD_TERMS):
            dread = _condense(entry.text)
        if not sweet and any(term in haystack for term in SWEET_TERMS):
            sweet = _condense(entry.text)
        if dread and sweet:
            break
    return CrossPackSignal(dread_subject=dread, sweet_subject=sweet)


__all__ = [
    "DREAD_TERMS",
    "SWEET_TERMS",
    "CrossPackSignal",
    "cross_pack_signal",
]
