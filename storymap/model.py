"""
Data model for storymap documents.

Status and UI colors are stored as plain dicts to allow user customization
and extension without code changes.
"""

from dataclasses import dataclass, field


DEFAULT_STATUS_COLORS: dict[str, str] = {
    "not-started": "#E0E0E0",  # grey
    "in-progress":  "#90CAF9",  # blue
    "done":         "#A5D6A7",  # green
    "blocked":      "#EF9A9A",  # red
}

DEFAULT_FALLBACK_STATUS_COLOR = "#FFFFFF"

DEFAULT_UI_COLORS: dict[str, str] = {
    "activity":       "#1565C0",  # dark blue  – background for activity headers
    "activity_text":  "#FFFFFF",  # white      – text on activity headers
    "task":           "#90CAF9",  # light blue – background for task headers
    "task_text":      "#0D47A1",  # dark blue  – text on task headers
    "release_header": "#CE93D8",  # light purple
    "release_text":   "#4A148C",  # dark purple
}


@dataclass
class Story:
    """
    A single user story within a task and release.

    Fields are stored as a free-form dict so that new [key:: value]
    annotations (status, persona, deadline, …) can be added without
    changing the model.
    """

    name: str
    description: str = ""
    fields: dict[str, str] = field(default_factory=dict)

    def status(self) -> str:
        return self.fields.get("status", "not-started")

    def status_color(
        self,
        color_map: dict[str, str] = DEFAULT_STATUS_COLORS,
        fallback: str = DEFAULT_FALLBACK_STATUS_COLOR,
    ) -> str:
        return color_map.get(self.status(), fallback)


@dataclass
class Task:
    """
    A task belonging to an activity.

    story_groups is a list of lists indexed by release position:
    story_groups[0] → stories in Release 1
    story_groups[1] → stories in Release 2
    …
    Empty lists represent releases with no stories for this task.
    """

    name: str
    story_groups: list[list[Story]] = field(default_factory=list)

    def stories_for_release(self, release_index: int) -> list[Story]:
        if release_index < len(self.story_groups):
            return self.story_groups[release_index]
        return []


@dataclass
class Activity:
    """Top-level grouping of related tasks."""

    name: str
    tasks: list[Task] = field(default_factory=list)


@dataclass
class Release:
    """A release/swimlane with an optional markdown description."""

    name: str
    description: str = ""


@dataclass
class Persona:
    """
    A UX persona with a full markdown description.

    The description may contain lists, links, and pandoc-style
    image references (e.g. ![Margie](margie.jpg){width=200px}).
    """

    name: str
    description: str = ""


@dataclass
class StorymapDocument:
    """Root document containing all sections."""

    releases: list[Release] = field(default_factory=list)
    personas: list[Persona] = field(default_factory=list)
    activities: list[Activity] = field(default_factory=list)
