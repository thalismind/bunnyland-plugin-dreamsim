from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    LightComponent,
    RoomComponent,
    WorldActor,
    spawn_entity,
)

from bunnyland_dreamsim import assess_sleep, spawn_bed


def _room(world, *, safe=True, title="Bedroom"):
    return spawn_entity(world, [RoomComponent(title=title, safe=safe)])


def _sleeper(world, room, name="Vin"):
    character = spawn_entity(
        world, [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return character


def _threat(world, room, name="wraith"):
    enemy = spawn_entity(world, [IdentityComponent(name=name, kind="character", tags=("hostile",))])
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), enemy.id)
    return enemy


def test_safe_bedroom_with_bed_is_comfortable():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)
    spawn_bed(actor.world, room_id=room.id, comfort=0.8)

    conditions = assess_sleep(actor.world, sleeper)

    assert conditions.room_safe is True
    assert conditions.dangerous is False
    assert conditions.comfortable is True
    assert conditions.bed_comfort == 0.8
    assert conditions.room_title == "Bedroom"


def test_threat_in_room_is_dangerous():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)
    _threat(actor.world, room, name="grendel")

    conditions = assess_sleep(actor.world, sleeper)

    assert conditions.has_threat is True
    assert conditions.threat == "grendel"
    assert conditions.dangerous is True


def test_unsafe_room_is_dangerous_without_a_threat():
    actor = WorldActor()
    room = _room(actor.world, safe=False, title="Crypt")
    sleeper = _sleeper(actor.world, room)

    conditions = assess_sleep(actor.world, sleeper)

    assert conditions.room_safe is False
    assert conditions.dangerous is True
    assert conditions.threat == ""


def test_dark_room_is_dangerous():
    actor = WorldActor()
    room = _room(actor.world)
    from bunnyland.core.ecs import replace_component

    replace_component(room, LightComponent(level=0.05, enabled=True))
    sleeper = _sleeper(actor.world, room)

    conditions = assess_sleep(actor.world, sleeper)

    assert conditions.dark is True
    assert conditions.dangerous is True


def test_disabled_light_counts_as_dark():
    actor = WorldActor()
    room = _room(actor.world)
    from bunnyland.core.ecs import replace_component

    replace_component(room, LightComponent(level=1.0, enabled=False))
    sleeper = _sleeper(actor.world, room)

    assert assess_sleep(actor.world, sleeper).dark is True


def test_best_bed_comfort_wins():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)
    spawn_bed(actor.world, room_id=room.id, comfort=0.3)
    spawn_bed(actor.world, room_id=room.id, comfort=0.9)

    assert assess_sleep(actor.world, sleeper).bed_comfort == 0.9


def test_uncontained_sleeper_sleeps_in_the_open():
    actor = WorldActor()
    sleeper = spawn_entity(
        actor.world, [IdentityComponent(name="drifter", kind="character"), CharacterComponent()]
    )

    conditions = assess_sleep(actor.world, sleeper)

    assert conditions.room_title == "the open"
    assert conditions.dangerous is False
    assert conditions.bed_comfort == 0.0
