"""Dream, rest, and furniture components.

Components are immutable (frozen pydantic dataclasses over ``relics.Component``); the
consequences swap whole values with ``replace_component(entity, replace(component, ...))``.

- :class:`DreamComponent` lives on a **character** and records the one dream they are
  currently having (or last had). It is first-person-only in prompts — dreams are private.
- :class:`RestQualityComponent` also lives on a character and grades their current rest.
- :class:`BedComponent` lives on a **bed** entity in a room and supplies the comfort that
  lifts rest quality.
"""

from __future__ import annotations

from bunnyland.core import SleepingComponent
from bunnyland.prompts.context import ComponentPromptContext
from pydantic.dataclasses import dataclass
from relics import Component

#: Dream flavours.
PLEASANT = "pleasant"
NIGHTMARE = "nightmare"


@dataclass(frozen=True)
class DreamComponent(Component):
    """The dream a character is having, or the one they woke remembering.

    ``sleep_started`` keys the dream to a single sleep session (the sleeper's
    ``SleepingComponent.started_at_epoch``) so the dream consequence knows when to compose a
    fresh dream versus letting the current one stand.
    """

    summary: str = "nothing you can hold onto"
    text: str = ""
    kind: str = PLEASANT
    quality: float = 0.5
    based_on_memory: str = ""
    omen: str = ""
    sleep_started: int = 0
    created_at_epoch: int = 0

    @property
    def is_nightmare(self) -> bool:
        return self.kind == NIGHTMARE

    def prompt_fragments(self, ctx: ComponentPromptContext) -> tuple[str, ...]:
        """Render the dream, first-person only (a dream is private to its dreamer).

        While the dreamer is still asleep the line is present-tense; once they have woken
        (the ``SleepingComponent`` is gone) it becomes the classic "You wake from a dream
        of ..." recall line.
        """
        if not ctx.is_first_person:
            return ()
        asleep = ctx.entity.has_component(SleepingComponent)
        article = "a nightmare" if self.is_nightmare else "a dream"
        lines: list[str] = []
        if asleep:
            verb = "caught in a nightmare" if self.is_nightmare else "dreaming"
            lines.append(f"You are {verb} of {self.summary}.")
        else:
            lines.append(f"You wake from {article} of {self.summary}.")
        if self.based_on_memory:
            lines.append(f"An old memory returns to you: {self.based_on_memory}")
        if self.omen:
            lines.append(f"An omen lingers from the dream: {self.omen}")
        return tuple(lines)


@dataclass(frozen=True)
class RestQualityComponent(Component):
    """How well a character is resting right now (derived from bed + room safety).

    ``recovery`` is a 0..1 multiplier other systems (e.g. a fatigue need) can read to scale
    how fast the sleeper recovers; better rest recovers faster.
    """

    quality: float = 0.5
    comfort: float = 0.0
    safe: bool = True
    recovery: float = 0.5
    updated_at_epoch: int = 0

    def prompt_fragments(self, ctx: ComponentPromptContext) -> tuple[str, ...]:
        if not ctx.is_first_person or not ctx.entity.has_component(SleepingComponent):
            return ()
        if self.quality >= 0.75:
            return ("You are resting deeply and well.",)
        if self.quality <= 0.35:
            return ("You are sleeping fitfully and poorly.",)
        return ("You are resting lightly.",)


@dataclass(frozen=True)
class BedComponent(Component):
    """A bed. Its ``comfort`` (0..1) lifts the rest quality of anyone sleeping in the room."""

    comfort: float = 0.6
    warmth: float = 0.5


__all__ = [
    "NIGHTMARE",
    "PLEASANT",
    "BedComponent",
    "DreamComponent",
    "RestQualityComponent",
]
