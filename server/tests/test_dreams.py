from __future__ import annotations

from bunnyland.core import (
    AffectComponent,
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    MemoryProfileComponent,
    RoomComponent,
    SleepingComponent,
    WorldActor,
    spawn_entity,
)
from bunnyland.core.components import ThoughtComponent
from bunnyland.core.ecs import replace_component
from bunnyland.core.edges import HasThought
from bunnyland.memory import InMemoryStore

from bunnyland_dreamsim import (
    NIGHTMARE,
    PLEASANT,
    DreamComponent,
    DreamComposedEvent,
    DreamConsequence,
    NightmareEvent,
)

EPOCH = 1000
COLLECTION = "vin-notes"


def _room(world, *, safe=True, title="Bedroom"):
    return spawn_entity(world, [RoomComponent(title=title, safe=safe)])


def _sleeper(world, room, *, name="Vin", started=0, profile=False, affect=False):
    components = [IdentityComponent(name=name, kind="character"), CharacterComponent()]
    if profile:
        components.append(MemoryProfileComponent(vector_collection=COLLECTION))
    if affect:
        components.append(AffectComponent())
    character = spawn_entity(world, components)
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    replace_component(character, SleepingComponent(started_at_epoch=started))
    return character


def _threat(world, room, name="wraith"):
    enemy = spawn_entity(world, [IdentityComponent(name=name, kind="character", tags=("hostile",))])
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), enemy.id)
    return enemy


def _thoughts(world, character):
    deltas = []
    for _edge, thought_id in character.get_relationships(HasThought):
        deltas.append(world.get_entity(thought_id).get_component(ThoughtComponent).affect_delta)
    return deltas


# -- mechanic 1: dream on sleep --------------------------------------------------------


def test_a_sleeping_character_dreams():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)

    DreamConsequence(onset=0).process(actor.world, EPOCH)

    assert sleeper.has_component(DreamComponent)
    dream = sleeper.get_component(DreamComponent)
    assert dream.text
    assert dream.created_at_epoch == EPOCH
    assert dream.sleep_started == 0


def test_no_dream_before_the_onset_delay():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room, started=EPOCH)

    DreamConsequence(onset=300).process(actor.world, EPOCH + 100)

    assert not sleeper.has_component(DreamComponent)


def test_awake_non_character_and_character_gating():
    actor = WorldActor()
    room = _room(actor.world)
    # awake character: no SleepingComponent -> never in the query, so no dream
    awake = spawn_entity(
        actor.world, [IdentityComponent(name="Kell", kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), awake.id)

    DreamConsequence(onset=0).process(actor.world, EPOCH)

    assert not awake.has_component(DreamComponent)


def test_dream_persists_after_waking_for_recall():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)
    DreamConsequence(onset=0).process(actor.world, EPOCH)
    assert sleeper.has_component(DreamComponent)

    sleeper.remove_component(SleepingComponent)

    assert sleeper.has_component(DreamComponent)  # remembered on waking


# -- cadence ---------------------------------------------------------------------------


def test_no_re_dream_within_the_interval():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)
    consequence = DreamConsequence(onset=0, interval=1800)

    consequence.process(actor.world, EPOCH)
    first = sleeper.get_component(DreamComponent)
    consequence.process(actor.world, EPOCH + 10)

    assert sleeper.get_component(DreamComponent) == first


def test_re_dreams_after_the_interval():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)
    consequence = DreamConsequence(onset=0, interval=1800)

    consequence.process(actor.world, EPOCH)
    first = sleeper.get_component(DreamComponent)
    consequence.process(actor.world, EPOCH + 2000)

    assert sleeper.get_component(DreamComponent).created_at_epoch == EPOCH + 2000
    assert sleeper.get_component(DreamComponent) != first


def test_a_new_sleep_session_dreams_afresh():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)
    consequence = DreamConsequence(onset=0, interval=100000)

    consequence.process(actor.world, EPOCH)
    # a brand new sleep session (re-slept) resets the cadence
    replace_component(sleeper, SleepingComponent(started_at_epoch=EPOCH + 5))
    consequence.process(actor.world, EPOCH + 5)

    assert sleeper.get_component(DreamComponent).sleep_started == EPOCH + 5


# -- mechanic 3: nightmare vs pleasant -------------------------------------------------


def test_safe_sleep_is_a_pleasant_dream():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)

    DreamConsequence(onset=0).process(actor.world, EPOCH)

    assert sleeper.get_component(DreamComponent).kind == PLEASANT


def test_threatened_sleep_is_a_nightmare():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)
    _threat(actor.world, room, name="grendel")

    DreamConsequence(onset=0).process(actor.world, EPOCH)

    dream = sleeper.get_component(DreamComponent)
    assert dream.kind == NIGHTMARE
    assert dream.omen  # foreshadowing line
    assert "grendel" in dream.summary
    assert dream.quality < 0.5


def test_nightmare_shifts_mood_toward_fear():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room, affect=True)
    _threat(actor.world, room)

    DreamConsequence(onset=0).process(actor.world, EPOCH)

    deltas = _thoughts(actor.world, sleeper)
    assert deltas and all(d.fear > 0 for d in deltas)


def test_pleasant_dream_shifts_mood_toward_contentment():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room, affect=True)

    DreamConsequence(onset=0).process(actor.world, EPOCH)

    deltas = _thoughts(actor.world, sleeper)
    assert deltas and all(d.valence > 0 for d in deltas)


def test_no_mood_thought_without_affect_component():
    actor = WorldActor()
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room)

    DreamConsequence(onset=0).process(actor.world, EPOCH)

    assert _thoughts(actor.world, sleeper) == []


# -- mechanic 2: memory-fed dreams + insight -------------------------------------------


def test_dream_is_woven_from_recent_memories():
    actor = WorldActor()
    store = InMemoryStore()
    store.add(COLLECTION, text="riding the ferris wheel", created_at_epoch=1)
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room, profile=True)

    DreamConsequence(store=store, onset=0).process(actor.world, EPOCH)

    assert "ferris wheel" in sleeper.get_component(DreamComponent).summary


def test_dream_is_recorded_as_a_private_memory():
    actor = WorldActor()
    store = InMemoryStore()
    room = _room(actor.world)
    _sleeper(actor.world, room, profile=True)

    DreamConsequence(store=store, onset=0).process(actor.world, EPOCH)

    recent = store.search(COLLECTION, mode="recent", limit=10)
    assert any(entry.source == "dream" for entry in recent)


def test_pleasant_dream_resurfaces_an_older_memory():
    actor = WorldActor()
    store = InMemoryStore()
    # Added oldest-first, so "the origin" is the oldest of the recent set.
    for text in ("the origin", "a middling day", "a recent day"):
        store.add(COLLECTION, text=text, created_at_epoch=1)
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room, profile=True)

    DreamConsequence(store=store, onset=0).process(actor.world, EPOCH)

    assert sleeper.get_component(DreamComponent).based_on_memory == "the origin"


def test_dreams_do_not_feed_on_their_own_dream_notes():
    actor = WorldActor()
    store = InMemoryStore()
    store.add(COLLECTION, text="a walk in the meadow", created_at_epoch=1)
    store.add(
        COLLECTION,
        text="a false dream note",
        tags=("dream",),
        source="dream",
        created_at_epoch=2,
    )
    room = _room(actor.world)
    sleeper = _sleeper(actor.world, room, profile=True)

    DreamConsequence(store=store, onset=0).process(actor.world, EPOCH)

    dream = sleeper.get_component(DreamComponent)
    assert "meadow" in dream.summary
    assert "false dream note" not in dream.summary


def test_no_store_still_dreams_from_room_alone():
    actor = WorldActor()
    room = _room(actor.world, title="Loft")
    sleeper = _sleeper(actor.world, room)

    DreamConsequence(store=None, onset=0).process(actor.world, EPOCH)

    assert "Loft" in sleeper.get_component(DreamComponent).summary


# -- events ----------------------------------------------------------------------------


def test_pleasant_dream_emits_only_a_composed_event():
    actor = WorldActor()
    room = _room(actor.world)
    _sleeper(actor.world, room)

    events = DreamConsequence(onset=0).process(actor.world, EPOCH)

    assert any(isinstance(e, DreamComposedEvent) and e.kind == PLEASANT for e in events)
    assert not any(isinstance(e, NightmareEvent) for e in events)


def test_nightmare_emits_a_nightmare_event():
    actor = WorldActor()
    room = _room(actor.world)
    _sleeper(actor.world, room)
    _threat(actor.world, room, name="grendel")

    events = DreamConsequence(onset=0).process(actor.world, EPOCH)

    nightmares = [e for e in events if isinstance(e, NightmareEvent)]
    assert len(nightmares) == 1
    assert "grendel" in nightmares[0].summary
    assert nightmares[0].omen
