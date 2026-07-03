from __future__ import annotations

from bunnyland.core.components import AffectVector

from bunnyland_dreamsim import NIGHTMARE, PLEASANT, SleepConditions, compose_dream
from bunnyland_dreamsim.composer import DreamDraft


def _safe(**kw):
    return SleepConditions(room_title="Bedroom", room_safe=True, bed_comfort=0.6, **kw)


def _dangerous(**kw):
    return SleepConditions(room_title="Crypt", room_safe=False, **kw)


def test_composition_is_deterministic_for_same_inputs():
    memories = ["a walk by the river", "an old friend", "a warm meal"]
    a = compose_dream(_safe(), memories, None, "char_1:0:500")
    b = compose_dream(_safe(), memories, None, "char_1:0:500")
    assert a == b


def test_different_seed_keys_can_differ_but_stay_stable():
    memories = ["the river", "the friend", "the meal"]
    first = compose_dream(_safe(), memories, None, "char_1:0:500")
    again = compose_dream(_safe(), memories, None, "char_1:0:500")
    other = compose_dream(_safe(), memories, None, "char_1:0:900")
    assert first == again
    assert isinstance(other, DreamDraft)


def test_safe_sleep_is_pleasant_and_has_no_omen():
    draft = compose_dream(_safe(), ["a walk by the river"], None, "c_1:0:1")
    assert draft.kind == PLEASANT
    assert draft.omen == ""
    assert draft.quality > 0.5


def test_dangerous_sleep_is_a_nightmare_with_an_omen():
    draft = compose_dream(_dangerous(threat="wraith"), [], None, "c_1:0:1")
    assert draft.kind == NIGHTMARE
    assert "wraith" in draft.omen
    assert "wraith" in draft.summary
    assert draft.quality < 0.5


def test_darkness_alone_breeds_a_nightmare():
    draft = compose_dream(
        SleepConditions(room_title="Cellar", room_safe=True, dark=True), [], None, "c_1:0:1"
    )
    assert draft.kind == NIGHTMARE
    assert draft.omen  # a foreshadowing line, even without a named threat


def test_pleasant_dream_resurfaces_the_oldest_memory_as_insight():
    # memories are newest-first; the oldest ("the origin") should return as an insight.
    memories = ["a recent day", "a middling day", "the origin"]
    draft = compose_dream(_safe(), memories, None, "c_1:0:1")
    assert draft.kind == PLEASANT
    assert draft.based_on_memory == "the origin"
    assert draft.summary != "the origin"  # subject and insight are distinct memories


def test_single_memory_yields_no_insight():
    draft = compose_dream(_safe(), ["only this"], None, "c_1:0:1")
    assert draft.based_on_memory == ""
    assert "only this" in draft.summary


def test_no_memories_falls_back_to_the_room():
    draft = compose_dream(_safe(), [], None, "c_1:0:1")
    assert "Bedroom" in draft.summary


def test_mood_word_reflects_affect():
    afraid = AffectVector(fear=12.0)
    draft = compose_dream(_dangerous(threat="beast"), [], afraid, "c_1:0:1")
    assert "uneasy" in draft.text


def test_hook_can_enrich_text_without_changing_the_kind():
    def hook(draft, conditions):
        return f"[enriched] {draft.summary}"

    draft = compose_dream(_safe(), ["a walk by the river"], None, "c_1:0:1", hook=hook)
    assert draft.text.startswith("[enriched]")
    assert draft.kind == PLEASANT


def test_empty_and_whitespace_memories_are_ignored():
    draft = compose_dream(_safe(), ["   ", ""], None, "c_1:0:1")
    assert "Bedroom" in draft.summary  # treated as no usable memories
