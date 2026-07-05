from __future__ import annotations

from bunnyland.memory import MemoryEntry

from bunnyland_dreamsim import CrossPackSignal, cross_pack_signal


def _entry(text, *, tags=(), source="manual"):
    return MemoryEntry(id="m", text=text, tags=tags, source=source)


def test_empty_entries_yield_an_empty_signal():
    signal = cross_pack_signal([])
    assert signal == CrossPackSignal()
    assert not signal.has_dread
    assert not signal.has_sweet


def test_a_fright_memory_becomes_a_dread_subject():
    signal = cross_pack_signal([_entry("a cryptid crossed the road at dusk")])
    assert signal.has_dread
    assert signal.dread_subject == "a cryptid crossed the road at"
    assert not signal.has_sweet


def test_a_celebration_memory_becomes_a_sweet_subject():
    signal = cross_pack_signal([_entry("the autumn festival filled the square")])
    assert signal.has_sweet
    assert signal.sweet_subject == "the autumn festival filled the square"
    assert not signal.has_dread


def test_a_tag_or_source_can_carry_the_signal():
    signal = cross_pack_signal([_entry("an ordinary evening", tags=("haunting",))])
    assert signal.has_dread
    signal2 = cross_pack_signal([_entry("an ordinary evening", source="festival")])
    assert signal2.has_sweet


def test_newest_matching_memory_wins_each_direction():
    # entries are newest-first
    entries = [
        _entry("a later cryptid sighting"),
        _entry("an earlier haunting"),
    ]
    signal = cross_pack_signal(entries)
    assert signal.dread_subject == "a later cryptid sighting"


def test_both_directions_latch_and_stop_scanning():
    entries = [
        _entry("a cryptid at the fence"),
        _entry("the harvest festival"),
        _entry("another festival later ignored"),
    ]
    signal = cross_pack_signal(entries)
    assert signal.dread_subject == "a cryptid at the fence"
    assert signal.sweet_subject == "the harvest festival"


def test_a_blank_memory_condenses_to_a_placeholder():
    signal = cross_pack_signal([_entry("   ", tags=("dread",))])
    assert signal.dread_subject == "something half-remembered"


def test_an_unremarkable_memory_produces_no_signal():
    signal = cross_pack_signal([_entry("a quiet cup of tea")])
    assert signal == CrossPackSignal()
