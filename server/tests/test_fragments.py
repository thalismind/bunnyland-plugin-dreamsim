from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    RoomComponent,
    SleepingComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.ecs import replace_component
from bunnyland.prompts.context import ComponentPromptContext, PromptPerspective

from bunnyland_dreamsim import (
    NIGHTMARE,
    PLEASANT,
    DreamComponent,
    RestQualityComponent,
    dreamsim_fragments,
)


def _character(world, name="Vin"):
    room = spawn_entity(world, [RoomComponent(title="Bedroom")])
    character = spawn_entity(
        world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return character


def _asleep(character, started=0):
    replace_component(character, SleepingComponent(started_at_epoch=started))


def test_sleeping_character_reads_present_tense_dream():
    actor = WorldActor()
    character = _character(actor.world)
    _asleep(character)
    replace_component(
        character, DreamComponent(summary="a walk by the river", kind=PLEASANT)
    )

    lines = dreamsim_fragments(actor.world, character)

    assert "You are dreaming of a walk by the river." in lines


def test_sleeping_character_reads_a_nightmare_line():
    actor = WorldActor()
    character = _character(actor.world)
    _asleep(character)
    replace_component(character, DreamComponent(summary="the wraith", kind=NIGHTMARE))

    lines = dreamsim_fragments(actor.world, character)

    assert "You are caught in a nightmare of the wraith." in lines


def test_woken_character_recalls_the_dream():
    actor = WorldActor()
    character = _character(actor.world)  # not asleep
    replace_component(
        character, DreamComponent(summary="a walk by the river", kind=PLEASANT)
    )

    lines = dreamsim_fragments(actor.world, character)

    assert "You wake from a dream of a walk by the river." in lines


def test_insight_and_omen_lines_surface():
    actor = WorldActor()
    character = _character(actor.world)
    replace_component(
        character,
        DreamComponent(
            summary="the crypt",
            kind=NIGHTMARE,
            based_on_memory="the day you first arrived",
            omen="the wraith is coming for you",
        ),
    )

    lines = dreamsim_fragments(actor.world, character)

    assert any("An old memory returns to you: the day you first arrived" in ln for ln in lines)
    assert any("An omen lingers from the dream: the wraith is coming for you" in ln for ln in lines)


def test_rest_quality_line_shows_while_asleep():
    actor = WorldActor()
    character = _character(actor.world)
    _asleep(character)
    replace_component(character, RestQualityComponent(quality=0.85))

    lines = dreamsim_fragments(actor.world, character)

    assert "You are resting deeply and well." in lines


def test_poor_rest_line():
    actor = WorldActor()
    character = _character(actor.world)
    _asleep(character)
    replace_component(character, RestQualityComponent(quality=0.2))

    assert "You are sleeping fitfully and poorly." in dreamsim_fragments(actor.world, character)


def test_rest_quality_is_hidden_while_awake():
    actor = WorldActor()
    character = _character(actor.world)  # awake
    replace_component(character, RestQualityComponent(quality=0.85))

    assert dreamsim_fragments(actor.world, character) == []


def test_no_dream_or_rest_yields_no_lines():
    actor = WorldActor()
    character = _character(actor.world)

    assert dreamsim_fragments(actor.world, character) == []


def test_dream_is_private_to_third_person_viewers():
    actor = WorldActor()
    dreamer = _character(actor.world, name="Vin")
    onlooker = _character(actor.world, name="Kell")
    _asleep(dreamer)
    replace_component(dreamer, DreamComponent(summary="a secret", kind=PLEASANT))

    ctx = ComponentPromptContext.for_entity(
        actor.world, dreamer, perspective=PromptPerspective(viewer=onlooker)
    )

    assert dreamer.get_component(DreamComponent).prompt_fragments(ctx) == ()
