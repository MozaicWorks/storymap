"""Tests for the storymap data model."""

import pytest
from storymap.model import (
    Activity,
    DEFAULT_FALLBACK_STATUS_COLOR,
    DEFAULT_STATUS_COLORS,
    DEFAULT_UI_COLORS,
    Persona,
    Release,
    Story,
    StorymapDocument,
    Task,
)


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------


class TestStory:
    def test_name_is_required(self):
        story = Story(name="As a user I want to log in")
        assert story.name == "As a user I want to log in"

    def test_description_defaults_to_empty(self):
        story = Story(name="Login")
        assert story.description == ""

    def test_fields_defaults_to_empty_dict(self):
        story = Story(name="Login")
        assert story.fields == {}

    def test_status_defaults_to_not_started(self):
        story = Story(name="Login")
        assert story.status() == "not-started"

    def test_status_reflects_fields(self):
        story = Story(name="Login", fields={"status": "done"})
        assert story.status() == "done"

    def test_status_color_for_known_status(self):
        for status, expected_color in DEFAULT_STATUS_COLORS.items():
            story = Story(name="s", fields={"status": status})
            assert story.status_color() == expected_color

    def test_status_color_for_unknown_status_returns_fallback(self):
        story = Story(name="s", fields={"status": "custom-status"})
        assert story.status_color() == DEFAULT_FALLBACK_STATUS_COLOR

    def test_status_color_with_custom_color_map(self):
        custom_map = {"custom-status": "#123456"}
        story = Story(name="s", fields={"status": "custom-status"})
        assert story.status_color(color_map=custom_map) == "#123456"

    def test_status_color_with_custom_fallback(self):
        story = Story(name="s", fields={"status": "unknown"})
        assert story.status_color(fallback="#AABBCC") == "#AABBCC"

    def test_fields_can_store_persona(self):
        story = Story(name="s", fields={"persona": "Margie the Manager"})
        assert story.fields["persona"] == "Margie the Manager"

    def test_fields_can_store_deadline(self):
        story = Story(name="s", fields={"deadline": "2026-03-01"})
        assert story.fields["deadline"] == "2026-03-01"

    def test_fields_can_store_arbitrary_keys(self):
        story = Story(name="s", fields={"custom-key": "custom-value"})
        assert story.fields["custom-key"] == "custom-value"

    def test_description_can_contain_markdown(self):
        desc = "See [issue #42](https://github.com/org/repo/issues/42)"
        story = Story(name="s", description=desc)
        assert story.description == desc

    def test_multiple_fields(self):
        story = Story(
            name="s",
            fields={
                "status": "in-progress",
                "persona": "Dave the Developer",
                "deadline": "2026-06-01",
            },
        )
        assert story.status() == "in-progress"
        assert story.fields["persona"] == "Dave the Developer"
        assert story.fields["deadline"] == "2026-06-01"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------


class TestTask:
    def test_name_is_required(self):
        task = Task(name="Authentication")
        assert task.name == "Authentication"

    def test_story_groups_defaults_to_empty(self):
        task = Task(name="Authentication")
        assert task.story_groups == []

    def test_stories_for_release_returns_correct_group(self):
        s1 = Story(name="Login")
        s2 = Story(name="Logout")
        task = Task(name="Auth", story_groups=[[s1], [s2]])
        assert task.stories_for_release(0) == [s1]
        assert task.stories_for_release(1) == [s2]

    def test_stories_for_release_returns_empty_for_out_of_range(self):
        task = Task(name="Auth", story_groups=[[Story(name="Login")]])
        assert task.stories_for_release(5) == []

    def test_stories_for_release_returns_empty_when_no_groups(self):
        task = Task(name="Auth")
        assert task.stories_for_release(0) == []

    def test_story_group_can_contain_multiple_stories(self):
        s1 = Story(name="Login")
        s2 = Story(name="Remember me")
        task = Task(name="Auth", story_groups=[[s1, s2]])
        assert len(task.stories_for_release(0)) == 2

    def test_story_group_can_be_empty_for_a_release(self):
        s1 = Story(name="Login")
        task = Task(name="Auth", story_groups=[[s1], []])
        assert task.stories_for_release(1) == []


# ---------------------------------------------------------------------------
# Activity
# ---------------------------------------------------------------------------


class TestActivity:
    def test_name_is_required(self):
        activity = Activity(name="User Management")
        assert activity.name == "User Management"

    def test_tasks_defaults_to_empty(self):
        activity = Activity(name="User Management")
        assert activity.tasks == []

    def test_can_hold_multiple_tasks(self):
        t1 = Task(name="Login")
        t2 = Task(name="Registration")
        activity = Activity(name="Auth", tasks=[t1, t2])
        assert len(activity.tasks) == 2
        assert activity.tasks[0].name == "Login"


# ---------------------------------------------------------------------------
# Release
# ---------------------------------------------------------------------------


class TestRelease:
    def test_name_is_required(self):
        release = Release(name="MVP")
        assert release.name == "MVP"

    def test_description_defaults_to_empty(self):
        release = Release(name="MVP")
        assert release.description == ""

    def test_description_can_be_set(self):
        release = Release(name="MVP", description="First public release.")
        assert release.description == "First public release."

    def test_description_can_contain_markdown(self):
        desc = "Includes [login](https://github.com/...) feature."
        release = Release(name="MVP", description=desc)
        assert release.description == desc


# ---------------------------------------------------------------------------
# Persona
# ---------------------------------------------------------------------------


class TestPersona:
    def test_name_is_required(self):
        persona = Persona(name="Margie the Manager")
        assert persona.name == "Margie the Manager"

    def test_description_defaults_to_empty(self):
        persona = Persona(name="Margie the Manager")
        assert persona.description == ""

    def test_description_can_contain_rich_markdown(self):
        desc = (
            "- **Age:** 45-55\n"
            "- **Tech level:** Low\n\n"
            "![Margie](margie.jpg){width=200px}\n\n"
            "[Interview notes](https://docs.google.com/...)"
        )
        persona = Persona(name="Margie the Manager", description=desc)
        assert persona.description == desc


# ---------------------------------------------------------------------------
# StorymapDocument
# ---------------------------------------------------------------------------


class TestStorymapDocument:
    def test_all_sections_default_to_empty(self):
        doc = StorymapDocument()
        assert doc.releases == []
        assert doc.personas == []
        assert doc.activities == []

    def test_title_defaults_to_none(self):
        doc = StorymapDocument()
        assert doc.title is None

    def test_description_defaults_to_empty(self):
        doc = StorymapDocument()
        assert doc.description == ""

    def test_title_can_be_set(self):
        doc = StorymapDocument(title="My Product")
        assert doc.title == "My Product"

    def test_description_can_be_set(self):
        doc = StorymapDocument(description="Short description.")
        assert doc.description == "Short description."

    def test_can_hold_releases(self):
        doc = StorymapDocument(releases=[Release(name="MVP"), Release(name="Beta")])
        assert len(doc.releases) == 2

    def test_can_hold_personas(self):
        doc = StorymapDocument(
            personas=[Persona(name="Margie"), Persona(name="Dave")]
        )
        assert len(doc.personas) == 2

    def test_can_hold_activities(self):
        doc = StorymapDocument(activities=[Activity(name="Auth")])
        assert len(doc.activities) == 1

    def test_full_document_structure(self):
        story = Story(
            name="Login",
            description="User can log in.",
            fields={"status": "done", "persona": "Margie the Manager"},
        )
        task = Task(name="Authentication", story_groups=[[story], []])
        activity = Activity(name="User Management", tasks=[task])
        doc = StorymapDocument(
            title="My Product",
            description="**Version:** 1.0",
            releases=[Release(name="MVP"), Release(name="Beta")],
            personas=[Persona(name="Margie the Manager", description="A manager.")],
            activities=[activity],
        )

        assert doc.title == "My Product"
        assert "Version" in doc.description
        assert len(doc.releases) == 2
        assert len(doc.personas) == 1
        assert len(doc.activities) == 1
        assert doc.activities[0].tasks[0].stories_for_release(0)[0].status() == "done"


# ---------------------------------------------------------------------------
# Default color constants
# ---------------------------------------------------------------------------


class TestDefaultColors:
    def test_all_known_statuses_have_colors(self):
        for status in ("not-started", "in-progress", "done", "blocked"):
            assert status in DEFAULT_STATUS_COLORS

    def test_status_colors_are_valid_hex(self):
        for color in DEFAULT_STATUS_COLORS.values():
            assert color.startswith("#")
            assert len(color) == 7

    def test_fallback_color_is_valid_hex(self):
        assert DEFAULT_FALLBACK_STATUS_COLOR.startswith("#")
        assert len(DEFAULT_FALLBACK_STATUS_COLOR) == 7

    def test_ui_colors_contain_expected_keys(self):
        for key in ("activity", "activity_text", "task", "task_text",
                    "release_header", "release_text"):
            assert key in DEFAULT_UI_COLORS

    def test_ui_colors_are_valid_hex(self):
        for color in DEFAULT_UI_COLORS.values():
            assert color.startswith("#")
            assert len(color) == 7
