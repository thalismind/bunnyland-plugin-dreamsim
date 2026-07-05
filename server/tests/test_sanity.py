from __future__ import annotations

from bunnyland.core import IdentityComponent, WorldActor, spawn_entity

from bunnyland_dreamsim import dread_subject
from bunnyland_dreamsim import sanity as sanity_module


def _character(world):
    return spawn_entity(world, [IdentityComponent(name="Vin", kind="character")])


def test_no_specter_pack_means_no_dread(monkeypatch):
    # Standalone: the guarded import failed, so dread is always empty.
    monkeypatch.setattr(sanity_module, "_SanityComponent", None)
    actor = WorldActor()
    assert dread_subject(_character(actor.world)) == ""


def test_a_stable_sleeper_carries_no_dread(monkeypatch):
    # Simulate the specter pack present with the character's IdentityComponent standing in
    # for a sanity component, and a band function reporting "stable".
    monkeypatch.setattr(sanity_module, "_SanityComponent", IdentityComponent)
    monkeypatch.setattr(sanity_module, "_sanity_band", lambda comp: "stable")
    monkeypatch.setattr(sanity_module, "_STABLE", "stable")
    actor = WorldActor()
    assert dread_subject(_character(actor.world)) == ""


def test_a_frayed_sleeper_carries_a_dread_subject(monkeypatch):
    monkeypatch.setattr(sanity_module, "_SanityComponent", IdentityComponent)
    monkeypatch.setattr(sanity_module, "_sanity_band", lambda comp: "frayed")
    monkeypatch.setattr(sanity_module, "_STABLE", "stable")
    actor = WorldActor()
    assert dread_subject(_character(actor.world)) == sanity_module.DREAD_SUBJECT


def test_no_sanity_component_means_no_dread(monkeypatch):
    # Pack present, but this character carries no sanity component.
    class _Sanity:
        pass

    monkeypatch.setattr(sanity_module, "_SanityComponent", _Sanity)
    actor = WorldActor()
    assert dread_subject(_character(actor.world)) == ""
