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
    A single user story within a task.

    Fields are stored as a free-form dict so that new [key:: value]
    annotations (status, persona, deadline, release, …) can be added without
    changing the model.

    The release a story belongs to is stored as fields["release"] and must
    match a release name defined in the Releases section.
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

    def release(self) -> str | None:
        return self.fields.get("release")


@dataclass
class Task:
    """A task belonging to an activity, containing a flat list of stories."""

    name: str
    stories: list[Story] = field(default_factory=list)

    def stories_for_release(self, release_key: str) -> list[Story]:
        """Return stories assigned to the given release key."""
        return [s for s in self.stories if s.release() == release_key]

    def unassigned_stories(self) -> list[Story]:
        """Return stories with no release field."""
        return [s for s in self.stories if s.release() is None]


@dataclass
class Activity:
    """Top-level grouping of related tasks."""

    name: str
    tasks: list[Task] = field(default_factory=list)


@dataclass
class Release:
    """A release/swimlane with an optional markdown description.

    If id is set, stories must use that value in [release:: id].
    If id is not set, stories use the release name directly.
    """

    name: str
    description: str = ""
    id: str | None = None

    def key(self) -> str:
        """The identifier used in [release:: ...] story fields."""
        return self.id if self.id is not None else self.name


@dataclass
class Persona:
    """
    A UX persona with a full markdown description.

    The description may contain lists, links, and image references.
    """

    name: str
    description: str = ""


@dataclass
class StorymapDocument:
    """Root document containing all sections."""

    title: str | None = None
    description: str = ""
    releases: list[Release] = field(default_factory=list)
    personas: list[Persona] = field(default_factory=list)
    activities: list[Activity] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
