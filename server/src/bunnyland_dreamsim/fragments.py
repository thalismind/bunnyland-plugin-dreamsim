"""Prompt fragment provider.

A single ``(world, character) -> list[str]`` provider feeds both the LLM actor context and
the human character-chat prompt. Dreams and rest are **private** to the sleeper, so this only
ever renders the *viewer's own* dream/rest components — never someone else's. Because those
components live on the character entity itself, the component context is naturally
first-person (``viewer == entity``), which is what :meth:`DreamComponent.prompt_fragments`
keys its "You are dreaming of ..." / "You wake from a dream of ..." wording on.
"""

from __future__ import annotations

from bunnyland.prompts.context import ComponentPromptContext
from relics import Entity, World

from .components import DreamComponent, RestQualityComponent

#: Components rendered for the viewer, in the order their lines should appear.
_SELF_COMPONENTS = (RestQualityComponent, DreamComponent)


def dreamsim_fragments(world: World, character: Entity) -> list[str]:
    ctx = ComponentPromptContext.for_entity(world, character)
    lines: list[str] = []
    for component_type in _SELF_COMPONENTS:
        if character.has_component(component_type):
            lines.extend(character.get_component(component_type).prompt_fragments(ctx))
    # Dedupe while preserving the dream's narrative order.
    return list(dict.fromkeys(lines))


__all__ = ["dreamsim_fragments"]
