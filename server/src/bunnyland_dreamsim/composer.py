"""Deterministically assemble a dream from a sleeper's state.

**No LLM, no network, no randomness, no wall-clock time.** A dream is a pure function of the
sleeping conditions, the sleeper's recent memories, their mood, and a stable seed key
(their id plus the epoch). The same inputs always yield the same dream, so tests run fully
offline. ``hashlib.sha256`` gives us a process-stable index (unlike ``hash()``), which keeps
the choice of template and memory reproducible across runs and machines.

A ``compose_dream`` caller may pass its own ``hook`` to enrich the text (e.g. a real model),
but the default path is entirely deterministic.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from bunnyland.core.components import AffectVector

from .components import NIGHTMARE, PLEASANT
from .conditions import SleepConditions

#: Pleasant dream templates, keyed on a ``{subject}`` phrase.
PLEASANT_TEMPLATES = (
    "a {mood} dream of {subject}, and it leaves you lighter",
    "a {mood} dream where {subject} drifts gently by",
    "a {mood} dream of {subject} that folds warmly around you",
)

#: Nightmare templates, keyed on a ``{subject}`` phrase.
NIGHTMARE_TEMPLATES = (
    "a {mood} nightmare of {subject} that will not let you go",
    "a {mood} nightmare where {subject} closes in from the dark",
    "a {mood} nightmare of {subject}, and you cannot wake",
)

#: Omen lines, keyed on a ``{threat}`` phrase.
OMEN_TEMPLATES = (
    "{threat} is coming for you",
    "beware {threat}",
    "{threat} will find this place",
)


@dataclass(frozen=True)
class DreamDraft:
    """The assembled dream, ready to write onto a :class:`DreamComponent`."""

    summary: str
    text: str
    kind: str
    quality: float
    based_on_memory: str = ""
    omen: str = ""


#: Type of an optional enrichment hook: (draft, conditions) -> replacement text.
DreamHook = Callable[["DreamDraft", SleepConditions], str]


def _seed_int(seed_key: str) -> int:
    """A process-stable non-negative integer from ``seed_key`` (never Python ``hash()``)."""
    digest = hashlib.sha256(seed_key.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _phrase(text: str) -> str:
    """Condense a memory into a short dream subject phrase."""
    words = text.strip().split()
    if not words:
        return "something half-remembered"
    return " ".join(words[:6]).rstrip(".!,;:").lower()


def _mood_word(affect: AffectVector | None) -> str:
    """A single deterministic mood adjective drawn from the strongest affect dimension."""
    if affect is None:
        return "quiet"
    if affect.fear >= 8.0:
        return "uneasy"
    if affect.sadness >= 8.0:
        return "wistful"
    if affect.anger >= 8.0:
        return "restless"
    if affect.valence >= 8.0:
        return "warm"
    return "quiet"


def compose_dream(
    conditions: SleepConditions,
    memories: Sequence[str],
    affect: AffectVector | None,
    seed_key: str,
    *,
    hook: DreamHook | None = None,
) -> DreamDraft:
    """Assemble a :class:`DreamDraft` from the sleeper's state.

    ``memories`` is ordered newest-first. A pleasant dream draws its subject from the most
    relevant memory and can resurface an *older* one as an insight; a nightmare fixates on
    the room's threat (or, lacking one, a recent memory twisted dark).
    """
    seed = _seed_int(seed_key)
    mood = _mood_word(affect)
    memory_texts = [text for text in memories if text.strip()]

    if conditions.dangerous:
        return _nightmare(conditions, memory_texts, mood, seed, hook)
    return _pleasant(conditions, memory_texts, mood, seed, hook)


def _apply_hook(
    draft: DreamDraft, conditions: SleepConditions, hook: DreamHook | None
) -> DreamDraft:
    if hook is None:
        return draft
    enriched = hook(draft, conditions)
    if not enriched:
        return draft
    return DreamDraft(
        summary=draft.summary,
        text=enriched,
        kind=draft.kind,
        quality=draft.quality,
        based_on_memory=draft.based_on_memory,
        omen=draft.omen,
    )


def _nightmare(
    conditions: SleepConditions,
    memories: list[str],
    mood: str,
    seed: int,
    hook: DreamHook | None,
) -> DreamDraft:
    if conditions.has_threat:
        subject = f"the {conditions.threat}"
        omen = OMEN_TEMPLATES[seed % len(OMEN_TEMPLATES)].format(threat=f"the {conditions.threat}")
    elif memories:
        subject = _phrase(memories[seed % len(memories)])
        omen = "something waits in the dark" if conditions.dark else "this is no place to rest"
    else:
        subject = "a formless dread"
        omen = "something waits in the dark" if conditions.dark else "this is no place to rest"
    text = NIGHTMARE_TEMPLATES[seed % len(NIGHTMARE_TEMPLATES)].format(mood=mood, subject=subject)
    draft = DreamDraft(
        summary=subject,
        text=text,
        kind=NIGHTMARE,
        quality=0.2,
        based_on_memory="",
        omen=omen,
    )
    return _apply_hook(draft, conditions, hook)


def _pleasant(
    conditions: SleepConditions,
    memories: list[str],
    mood: str,
    seed: int,
    hook: DreamHook | None,
) -> DreamDraft:
    # Insight: a pleasant dream draws its subject from a newer memory and can resurface the
    # *oldest* of the recent set (memories are newest-first) as a distinct older memory. To
    # keep subject and insight from ever being the same memory, the subject is chosen from all
    # but the last (oldest) entry whenever there are two or more.
    based_on = ""
    if not memories:
        subject = f"the {conditions.room_title}"
    elif len(memories) == 1:
        subject = _phrase(memories[0])
    else:
        subject = _phrase(memories[seed % (len(memories) - 1)])
        based_on = memories[-1].strip()
    text = PLEASANT_TEMPLATES[seed % len(PLEASANT_TEMPLATES)].format(mood=mood, subject=subject)
    draft = DreamDraft(
        summary=subject,
        text=text,
        kind=PLEASANT,
        quality=0.8,
        based_on_memory=based_on,
        omen="",
    )
    return _apply_hook(draft, conditions, hook)


__all__ = [
    "NIGHTMARE_TEMPLATES",
    "OMEN_TEMPLATES",
    "PLEASANT_TEMPLATES",
    "DreamDraft",
    "DreamHook",
    "compose_dream",
]
