"""Tests for the storymap parser."""

import pytest
from storymap.parser import (
    StorymapParser,
    _extract_lines,
    _parse_story_heading,
)
from storymap.model import StorymapDocument


# ---------------------------------------------------------------------------
# Fixtures — reusable markdown snippets
# ---------------------------------------------------------------------------

MINIMAL = """\
# Releases
## MVP

# Map
## User Management
### Login
#### Sign in
"""

FULL = """\
# Releases
## MVP
First public release.

## Beta
Testing with selected users.

# Personas
## Margie the Manager
- **Age:** 45-55
- **Tech level:** Low

She manages a team of 8.

## Dave the Developer
API-first mindset.

# Map
## User Management
### Authentication
#### Sign in [status:: done] [persona:: Margie the Manager]
User can log in with email and password.
See [issue #1](https://github.com/org/repo/issues/1)
---
#### Password reset [status:: in-progress] [deadline:: 2026-03-01]
### Profile
#### Edit profile
---
#### Upload avatar [status:: blocked]
Blocked by storage decision.
## Reporting
### Dashboard
#### View summary [status:: done]
---
"""


# ---------------------------------------------------------------------------
# _parse_story_heading (unit)
# ---------------------------------------------------------------------------


class TestParseStoryHeading:
    def test_no_fields(self):
        name, fields = _parse_story_heading("Sign in")
        assert name == "Sign in"
        assert fields == {}

    def test_single_field(self):
        name, fields = _parse_story_heading("Sign in [status:: done]")
        assert name == "Sign in"
        assert fields == {"status": "done"}

    def test_multiple_fields(self):
        name, fields = _parse_story_heading(
            "Sign in [status:: in-progress] [persona:: Margie the Manager]"
        )
        assert name == "Sign in"
        assert fields == {
            "status": "in-progress",
            "persona": "Margie the Manager",
        }

    def test_all_known_fields(self):
        name, fields = _parse_story_heading(
            "Story [status:: done] [persona:: Dave] [deadline:: 2026-06-01]"
        )
        assert name == "Story"
        assert fields["status"] == "done"
        assert fields["persona"] == "Dave"
        assert fields["deadline"] == "2026-06-01"

    def test_field_at_start_of_heading(self):
        # Edge case: field appears before the name (unusual but valid)
        name, fields = _parse_story_heading("[status:: done] Sign in")
        assert name == "Sign in"
        assert fields == {"status": "done"}

    def test_custom_field_key(self):
        name, fields = _parse_story_heading("Story [custom-key:: some value]")
        assert fields == {"custom-key": "some value"}

    def test_field_with_extra_whitespace(self):
        name, fields = _parse_story_heading("Story [status::   done  ]")
        assert fields == {"status": "done"}

    def test_name_whitespace_stripped(self):
        name, fields = _parse_story_heading("  Sign in  [status:: done]  ")
        assert name == "Sign in"

    def test_empty_name_with_only_fields(self):
        name, fields = _parse_story_heading("[status:: done]")
        assert name == ""
        assert fields == {"status": "done"}


# ---------------------------------------------------------------------------
# _extract_lines (unit)
# ---------------------------------------------------------------------------


class TestExtractLines:
    def test_basic_extraction(self):
        lines = ["line 0", "line 1", "line 2"]
        assert _extract_lines(lines, 1, 2) == "line 1"

    def test_multi_line(self):
        lines = ["a", "b", "c"]
        assert _extract_lines(lines, 0, 3) == "a\nb\nc"

    def test_empty_range(self):
        assert _extract_lines(["a", "b"], 1, 1) == ""

    def test_start_equals_end(self):
        assert _extract_lines(["a"], 0, 0) == ""

    def test_start_greater_than_end(self):
        assert _extract_lines(["a", "b"], 2, 1) == ""

    def test_strips_leading_blank_lines(self):
        lines = ["", "", "content", "more"]
        assert _extract_lines(lines, 0, 4) == "content\nmore"

    def test_strips_trailing_blank_lines(self):
        lines = ["content", "", ""]
        assert _extract_lines(lines, 0, 3) == "content"

    def test_strips_both_ends(self):
        lines = ["", "content", ""]
        assert _extract_lines(lines, 0, 3) == "content"

    def test_all_blank_returns_empty(self):
        lines = ["", "  ", ""]
        assert _extract_lines(lines, 0, 3) == ""

    def test_preserves_internal_blank_lines(self):
        lines = ["para 1", "", "para 2"]
        assert _extract_lines(lines, 0, 3) == "para 1\n\npara 2"


# ---------------------------------------------------------------------------
# StorymapParser — releases section
# ---------------------------------------------------------------------------


class TestParserReleases:
    def test_single_release_no_description(self):
        doc = StorymapParser().parse(MINIMAL)
        assert len(doc.releases) == 1
        assert doc.releases[0].name == "MVP"
        assert doc.releases[0].description == ""

    def test_multiple_releases(self):
        doc = StorymapParser().parse(FULL)
        assert len(doc.releases) == 2
        assert doc.releases[0].name == "MVP"
        assert doc.releases[1].name == "Beta"

    def test_release_description(self):
        doc = StorymapParser().parse(FULL)
        assert "First public release." in doc.releases[0].description

    def test_release_without_description_is_empty(self):
        src = "# Releases\n## MVP\n\n## Beta\n\n# Map\n## A\n### T\n#### S\n"
        doc = StorymapParser().parse(src)
        assert doc.releases[0].description == ""

    def test_release_description_with_markdown(self):
        src = (
            "# Releases\n"
            "## MVP\n"
            "Includes [login](#) and registration.\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert "[login](#)" in doc.releases[0].description


# ---------------------------------------------------------------------------
# StorymapParser — personas section
# ---------------------------------------------------------------------------


class TestParserPersonas:
    def test_multiple_personas(self):
        doc = StorymapParser().parse(FULL)
        assert len(doc.personas) == 2
        assert doc.personas[0].name == "Margie the Manager"
        assert doc.personas[1].name == "Dave the Developer"

    def test_persona_description(self):
        doc = StorymapParser().parse(FULL)
        assert "Age" in doc.personas[0].description
        assert "manages a team" in doc.personas[0].description

    def test_persona_rich_markdown(self):
        src = (
            "# Personas\n"
            "## Margie\n"
            "- **Age:** 45-55\n"
            "- **Tech:** Low\n\n"
            "![Margie](margie.jpg){width=200px}\n\n"
            "[Notes](https://docs.google.com/)\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert "![Margie](margie.jpg)" in doc.personas[0].description
        assert "[Notes]" in doc.personas[0].description

    def test_no_personas_section(self):
        doc = StorymapParser().parse(MINIMAL)
        assert doc.personas == []


# ---------------------------------------------------------------------------
# StorymapParser — map structure
# ---------------------------------------------------------------------------


class TestParserMapStructure:
    def test_single_activity(self):
        doc = StorymapParser().parse(MINIMAL)
        assert len(doc.activities) == 1
        assert doc.activities[0].name == "User Management"

    def test_multiple_activities(self):
        doc = StorymapParser().parse(FULL)
        assert len(doc.activities) == 2
        assert doc.activities[0].name == "User Management"
        assert doc.activities[1].name == "Reporting"

    def test_tasks_under_activity(self):
        doc = StorymapParser().parse(FULL)
        auth = doc.activities[0]
        assert len(auth.tasks) == 2
        assert auth.tasks[0].name == "Authentication"
        assert auth.tasks[1].name == "Profile"

    def test_single_task_single_story(self):
        doc = StorymapParser().parse(MINIMAL)
        task = doc.activities[0].tasks[0]
        assert task.name == "Login"
        assert len(task.story_groups) >= 1
        assert task.story_groups[0][0].name == "Sign in"

    def test_empty_map_section(self):
        src = "# Releases\n## MVP\n\n# Map\n"
        doc = StorymapParser().parse(src)
        assert doc.activities == []


# ---------------------------------------------------------------------------
# StorymapParser — release groups (--- separators)
# ---------------------------------------------------------------------------


class TestParserReleaseGroups:
    def test_no_separator_creates_one_group(self):
        src = (
            "# Releases\n## R1\n\n"
            "# Map\n## A\n### T\n"
            "#### Story 1\n"
        )
        doc = StorymapParser().parse(src)
        task = doc.activities[0].tasks[0]
        assert len(task.story_groups) == 1
        assert task.story_groups[0][0].name == "Story 1"

    def test_one_separator_creates_two_groups(self):
        src = (
            "# Releases\n## R1\n## R2\n\n"
            "# Map\n## A\n### T\n"
            "#### Story 1\n"
            "---\n"
            "#### Story 2\n"
        )
        doc = StorymapParser().parse(src)
        task = doc.activities[0].tasks[0]
        assert len(task.story_groups) == 2
        assert task.story_groups[0][0].name == "Story 1"
        assert task.story_groups[1][0].name == "Story 2"

    def test_separator_before_first_story_creates_empty_first_group(self):
        src = (
            "# Releases\n## R1\n## R2\n\n"
            "# Map\n## A\n### T\n"
            "---\n"
            "#### Story 1\n"
        )
        doc = StorymapParser().parse(src)
        task = doc.activities[0].tasks[0]
        assert task.story_groups[0] == []
        assert task.story_groups[1][0].name == "Story 1"

    def test_multiple_stories_in_one_group(self):
        src = (
            "# Releases\n## R1\n## R2\n\n"
            "# Map\n## A\n### T\n"
            "#### Story 1\n"
            "#### Story 2\n"
            "---\n"
            "#### Story 3\n"
        )
        doc = StorymapParser().parse(src)
        task = doc.activities[0].tasks[0]
        assert len(task.story_groups[0]) == 2
        assert task.story_groups[0][0].name == "Story 1"
        assert task.story_groups[0][1].name == "Story 2"
        assert task.story_groups[1][0].name == "Story 3"

    def test_separator_without_following_story_creates_empty_group(self):
        src = (
            "# Releases\n## R1\n## R2\n\n"
            "# Map\n## A\n### T\n"
            "#### Story 1\n"
            "---\n"
        )
        doc = StorymapParser().parse(src)
        task = doc.activities[0].tasks[0]
        assert task.story_groups[0][0].name == "Story 1"
        assert task.story_groups[1] == []

    def test_separator_resets_between_tasks(self):
        src = (
            "# Releases\n## R1\n## R2\n\n"
            "# Map\n## A\n"
            "### Task 1\n"
            "#### S1\n---\n#### S2\n"
            "### Task 2\n"
            "#### S3\n"
        )
        doc = StorymapParser().parse(src)
        t1 = doc.activities[0].tasks[0]
        t2 = doc.activities[0].tasks[1]
        assert len(t1.story_groups) == 2
        assert len(t2.story_groups) == 1
        assert t2.story_groups[0][0].name == "S3"


# ---------------------------------------------------------------------------
# StorymapParser — story fields and descriptions
# ---------------------------------------------------------------------------


class TestParserStoryFields:
    def test_story_without_fields(self):
        doc = StorymapParser().parse(MINIMAL)
        story = doc.activities[0].tasks[0].story_groups[0][0]
        assert story.fields == {}
        assert story.status() == "not-started"

    def test_story_status_field(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].story_groups[0][0]
        assert story.fields["status"] == "done"

    def test_story_persona_field(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].story_groups[0][0]
        assert story.fields["persona"] == "Margie the Manager"

    def test_story_deadline_field(self):
        doc = StorymapParser().parse(FULL)
        # "Password reset" is in release group 1 (after ---)
        story = doc.activities[0].tasks[0].story_groups[1][0]
        assert story.fields["deadline"] == "2026-03-01"

    def test_story_with_description(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].story_groups[0][0]
        assert "log in with email" in story.description

    def test_story_description_with_link(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].story_groups[0][0]
        assert "[issue #1]" in story.description

    def test_story_without_description_is_empty(self):
        doc = StorymapParser().parse(FULL)
        # "Password reset" has no description body
        story = doc.activities[0].tasks[0].story_groups[1][0]
        assert story.description == ""

    def test_story_name_strips_fields(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].story_groups[0][0]
        assert story.name == "Sign in"
        assert "[status" not in story.name

    def test_blocked_story_with_description(self):
        doc = StorymapParser().parse(FULL)
        # "Upload avatar" is in profile task, release group 1
        story = doc.activities[0].tasks[1].story_groups[1][0]
        assert story.name == "Upload avatar"
        assert story.fields["status"] == "blocked"
        assert "storage" in story.description


# ---------------------------------------------------------------------------
# StorymapParser — edge cases
# ---------------------------------------------------------------------------


class TestParserEdgeCases:
    def test_empty_string(self):
        doc = StorymapParser().parse("")
        assert doc == StorymapDocument()

    def test_only_releases_section(self):
        doc = StorymapParser().parse("# Releases\n## MVP\n")
        assert len(doc.releases) == 1
        assert doc.activities == []

    def test_section_names_case_insensitive(self):
        src = (
            "# RELEASES\n## MVP\n\n"
            "# PERSONAS\n## Dave\n\n"
            "# MAP\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert len(doc.releases) == 1
        assert len(doc.personas) == 1
        assert len(doc.activities) == 1

    def test_unknown_h1_section_is_ignored(self):
        src = (
            "# Introduction\nSome intro text.\n\n"
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert len(doc.releases) == 1

    def test_description_multiline(self):
        src = (
            "# Releases\n## R1\n\n"
            "# Map\n## A\n### T\n"
            "#### Story\n"
            "First paragraph.\n\n"
            "Second paragraph.\n"
        )
        doc = StorymapParser().parse(src)
        story = doc.activities[0].tasks[0].story_groups[0][0]
        assert "First paragraph." in story.description
        assert "Second paragraph." in story.description
