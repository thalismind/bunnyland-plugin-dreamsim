from __future__ import annotations

from bunnyland.core.components import AffectVector

from bunnyland_dreamsim import NIGHTMARE, PLEASANT, SleepConditions, compose_dream
from bunnyland_dreamsim.composer import DreamDraft
from bunnyland_dreamsim.connectors import CrossPackSignal


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


def test_each_affect_dimension_has_its_own_mood_word():
    cases = {
        AffectVector(sadness=9.0): "wistful",
        AffectVector(anger=9.0): "restless",
        AffectVector(valence=9.0): "warm",
        AffectVector(): "quiet",
    }
    for affect, word in cases.items():
        draft = compose_dream(_safe(), ["a walk"], affect, "c_1:0:1")
        assert word in draft.text


def test_a_dream_of_a_blank_forced_subject_condenses_to_a_placeholder():
    # a nightmare from an all-whitespace memory (dark, no threat) falls back gracefully
    draft = compose_dream(SleepConditions(room_title="Cellar", dark=True), ["   "], None, "c_1:0:1")
    assert draft.summary == "a formless dread"


def test_hook_can_enrich_text_without_changing_the_kind():
    def hook(draft, conditions):
        return f"[enriched] {draft.summary}"

    draft = compose_dream(_safe(), ["a walk by the river"], None, "c_1:0:1", hook=hook)
    assert draft.text.startswith("[enriched]")
    assert draft.kind == PLEASANT


def test_empty_and_whitespace_memories_are_ignored():
    draft = compose_dream(_safe(), ["   ", ""], None, "c_1:0:1")
    assert "Bedroom" in draft.summary  # treated as no usable memories


def test_hook_returning_empty_leaves_the_draft_untouched():
    draft = compose_dream(_safe(), ["a walk"], None, "c_1:0:1", hook=lambda d, c: "")
    assert "a walk" in draft.text  # empty enrichment is ignored, original text stands


# -- v2: cross-pack tone signal --------------------------------------------------------


def test_dread_signal_invades_even_a_safe_night():
    signal = CrossPackSignal(dread_subject="a cryptid at the treeline")
    draft = compose_dream(_safe(), ["a warm meal"], None, "c_1:0:1", signal=signal)
    assert draft.kind == NIGHTMARE
    assert draft.summary == "a cryptid at the treeline"
    assert "a cryptid at the treeline" in draft.omen


def test_sweet_signal_sweetens_a_safe_night_and_keeps_an_insight():
    signal = CrossPackSignal(sweet_subject="the harvest festival")
    memories = ["a recent day", "the origin"]
    draft = compose_dream(_safe(), memories, None, "c_1:0:1", signal=signal)
    assert draft.kind == PLEASANT
    assert draft.summary == "the harvest festival"
    assert draft.based_on_memory == "the origin"


def test_sweet_signal_yields_to_a_dangerous_night():
    signal = CrossPackSignal(sweet_subject="the harvest festival")
    draft = compose_dream(_dangerous(threat="wraith"), [], None, "c_1:0:1", signal=signal)
    assert draft.kind == NIGHTMARE  # danger overrides a sweet memory
    assert "wraith" in draft.summary


def test_dread_signal_wins_over_a_sweet_one():
    signal = CrossPackSignal(dread_subject="a haunting", sweet_subject="a feast")
    draft = compose_dream(_safe(), [], None, "c_1:0:1", signal=signal)
    assert draft.kind == NIGHTMARE
    assert draft.summary == "a haunting"


def test_dark_nightmare_from_a_recent_memory_when_unnamed():
    # dark + no named threat + memories -> the nightmare fixates on a memory twisted dark.
    draft = compose_dream(
        SleepConditions(room_title="Cellar", dark=True), ["a long hallway"], None, "c_1:0:1"
    )
    assert draft.kind == NIGHTMARE
    assert "hallway" in draft.summary
    assert draft.omen == "something waits in the dark"
