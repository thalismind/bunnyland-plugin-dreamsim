from __future__ import annotations

from bunnyland.core.world_actor import WorldActor
from bunnyland.plugins import apply_plugins, load_modules

from bunnyland_dreamsim import (
    BedComponent,
    DreamComponent,
    DreamOmenEvent,
    DreamsOf,
    DreamsRecalledEvent,
    MotifComponent,
    RecurringDreamEvent,
    RestQualityComponent,
    dreamsim_fragments,
)
from bunnyland_dreamsim.commands import RECALL_DREAMS
from bunnyland_dreamsim.plugin import PLUGIN_ID, plugin


def test_plugin_loads_with_module_qualified_id():
    plugins = load_modules(["bunnyland_dreamsim"])
    assert [p.id for p in plugins] == [PLUGIN_ID]


def test_plugin_is_versioned_v2():
    assert plugin().version == "0.2.0"


def test_plugin_declares_its_contributions():
    plugin = load_modules(["bunnyland_dreamsim"])[0]
    for component in (DreamComponent, RestQualityComponent, BedComponent, MotifComponent):
        assert component in plugin.ecs.components
    assert DreamsOf in plugin.ecs.edges
    assert dreamsim_fragments in plugin.content.prompt_fragments


def test_plugin_registers_v2_events_and_the_recall_verb():
    plugin = load_modules(["bunnyland_dreamsim"])[0]
    for event in (RecurringDreamEvent, DreamOmenEvent, DreamsRecalledEvent):
        assert event in plugin.commands.typed_events
    assert any(a.command_type == RECALL_DREAMS for a in plugin.commands.action_definitions)
    assert len(plugin.commands.action_handlers) == 1


def test_plugin_recommends_the_specter_pack_softly():
    plugin = load_modules(["bunnyland_dreamsim"])[0]
    assert "bunnyland.spectersim" in plugin.dependencies.recommends
    assert plugin.dependencies.requires == ()


def test_plugin_applies_and_registers_events():
    actor = WorldActor()
    applied = apply_plugins(load_modules(["bunnyland_dreamsim"]), actor)
    assert applied[0].id == PLUGIN_ID


def test_install_registers_two_consequences():
    actor = WorldActor()
    before = len(actor._consequences)
    apply_plugins(load_modules(["bunnyland_dreamsim"]), actor)
    assert len(actor._consequences) - before == 2
