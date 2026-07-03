from __future__ import annotations

from bunnyland.core.world_actor import WorldActor
from bunnyland.plugins import apply_plugins, load_modules

from bunnyland_dreamsim import (
    BedComponent,
    DreamComponent,
    RestQualityComponent,
    dreamsim_fragments,
)
from bunnyland_dreamsim.plugin import PLUGIN_ID


def test_plugin_loads_with_module_qualified_id():
    plugins = load_modules(["bunnyland_dreamsim"])
    assert [p.id for p in plugins] == [f"bunnyland_dreamsim.{PLUGIN_ID}"]


def test_plugin_declares_its_contributions():
    plugin = load_modules(["bunnyland_dreamsim"])[0]
    for component in (DreamComponent, RestQualityComponent, BedComponent):
        assert component in plugin.ecs.components
    assert dreamsim_fragments in plugin.content.prompt_fragments


def test_plugin_applies_and_registers_events():
    actor = WorldActor()
    applied = apply_plugins(load_modules(["bunnyland_dreamsim"]), actor)
    assert applied[0].id == f"bunnyland_dreamsim.{PLUGIN_ID}"


def test_install_registers_two_consequences():
    actor = WorldActor()
    before = len(actor._consequences)
    apply_plugins(load_modules(["bunnyland_dreamsim"]), actor)
    assert len(actor._consequences) - before == 2
