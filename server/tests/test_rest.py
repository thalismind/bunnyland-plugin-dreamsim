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

from bunnyland_dreamsim import (
    RestQualityComponent,
    RestQualityConsequence,
    SleepConditions,
    rest_quality_for,
    spawn_bed,
)

EPOCH = 1000


def _sleeping(world, room, *, name="Vin"):
    character = spawn_entity(
        world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    replace_component(character, SleepingComponent(started_at_epoch=0))
    return character


def _room(world, *, safe=True, title="Bedroom"):
    return spawn_entity(world, [RoomComponent(title=title, safe=safe)])


def test_comfortable_safe_bed_rests_well():
    quality = rest_quality_for(
        SleepConditions(room_title="Bedroom", room_safe=True, bed_comfort=0.8)
    )
    assert quality.quality == 0.82
    assert quality.safe is True
    assert quality.recovery == 0.82


def test_dangerous_sleep_rests_poorly():
    quality = rest_quality_for(SleepConditions(room_title="Crypt", room_safe=False))
    assert quality.quality < 0.35
    assert quality.safe is False


def test_safe_floor_sleep_is_middling():
    quality = rest_quality_for(SleepConditions(room_title="Hall", room_safe=True))
    assert quality.quality == 0.5


def test_consequence_grades_a_sleeping_character():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeping(actor.world, room)
    spawn_bed(actor.world, room_id=room.id, comfort=0.8)

    RestQualityConsequence().process(actor.world, EPOCH)

    rest = sleeper.get_component(RestQualityComponent)
    assert rest.quality == 0.82
    assert rest.updated_at_epoch == EPOCH
    assert rest.safe is True


def test_consequence_ignores_awake_characters():
    actor = WorldActor()
    room = _room(actor.world)
    character = spawn_entity(
        actor.world, [IdentityComponent(name="Kell", kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)

    RestQualityConsequence().process(actor.world, EPOCH)

    assert not character.has_component(RestQualityComponent)


def test_consequence_is_idempotent_within_a_tick():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeping(actor.world, room)
    consequence = RestQualityConsequence()

    consequence.process(actor.world, EPOCH)
    first = sleeper.get_component(RestQualityComponent)
    consequence.process(actor.world, EPOCH)
    assert sleeper.get_component(RestQualityComponent) == first
