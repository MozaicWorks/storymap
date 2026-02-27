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
#### Sign in [status:: done] [persona:: Margie the Manager] [release:: MVP]
User can log in with email and password.
See [issue #1](https://github.com/org/repo/issues/1)
#### Password reset [status:: in-progress] [deadline:: 2026-03-01] [release:: Beta]
### Profile
#### Edit profile [release:: MVP]
#### Upload avatar [status:: blocked] [release:: Beta]
Blocked by storage decision.
## Reporting
### Dashboard
#### View summary [status:: done] [release:: MVP]
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

    def test_release_field(self):
        name, fields = _parse_story_heading("Sign in [status:: done] [release:: MVP]")
        assert name == "Sign in"
        assert fields["release"] == "MVP"

    def test_all_known_fields(self):
        name, fields = _parse_story_heading(
            "Story [status:: done] [persona:: Dave] [deadline:: 2026-06-01] [release:: Beta]"
        )
        assert name == "Story"
        assert fields["status"] == "done"
        assert fields["persona"] == "Dave"
        assert fields["deadline"] == "2026-06-01"
        assert fields["release"] == "Beta"

    def test_field_at_start_of_heading(self):
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

    def test_release_id_field(self):
        src = "# Releases\n## My Long Release Name [id:: mvp]\n\n# Map\n## A\n### T\n#### S\n"
        doc = StorymapParser().parse(src)
        assert doc.releases[0].name == "My Long Release Name"
        assert doc.releases[0].id == "mvp"
        assert doc.releases[0].key() == "mvp"

    def test_release_without_id_uses_name_as_key(self):
        src = "# Releases\n## MVP\n\n# Map\n## A\n### T\n#### S\n"
        doc = StorymapParser().parse(src)
        assert doc.releases[0].id is None
        assert doc.releases[0].key() == "MVP"

    def test_release_id_stripped_from_display_name(self):
        src = "# Releases\n## Long Name [id:: short]\n\n# Map\n## A\n### T\n#### S\n"
        doc = StorymapParser().parse(src)
        assert "[id::" not in doc.releases[0].name

    def test_release_name_with_spaces_and_no_id_warns(self):
        src = "# Releases\n## My Long Release\n\n# Map\n## A\n### T\n#### S\n"
        doc = StorymapParser().parse(src)
        assert any("My Long Release" in w and "id::" in w for w in doc.warnings)

    def test_release_name_with_spaces_and_id_does_not_warn(self):
        src = "# Releases\n## My Long Release [id:: mlr]\n\n# Map\n## A\n### T\n#### S\n"
        doc = StorymapParser().parse(src)
        assert not any("id::" in w for w in doc.warnings)

    def test_release_name_without_spaces_does_not_warn(self):
        src = "# Releases\n## MVP\n\n# Map\n## A\n### T\n#### S\n"
        doc = StorymapParser().parse(src)
        assert doc.warnings == []

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
            "![Margie](margie.jpg)\n\n"
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
        assert len(task.stories) == 1
        assert task.stories[0].name == "Sign in"

    def test_empty_map_section(self):
        src = "# Releases\n## MVP\n\n# Map\n"
        doc = StorymapParser().parse(src)
        assert doc.activities == []


# ---------------------------------------------------------------------------
# StorymapParser — release field grouping
# ---------------------------------------------------------------------------


class TestParserReleaseField:
    def test_story_with_release_field(self):
        src = (
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n"
            "#### Story 1 [release:: MVP]\n"
        )
        doc = StorymapParser().parse(src)
        task = doc.activities[0].tasks[0]
        assert task.stories[0].release() == "MVP"

    def test_stories_for_release_filters_correctly(self):
        src = (
            "# Releases\n## MVP\n## Beta\n\n"
            "# Map\n## A\n### T\n"
            "#### Story 1 [release:: MVP]\n"
            "#### Story 2 [release:: Beta]\n"
            "#### Story 3 [release:: MVP]\n"
        )
        doc = StorymapParser().parse(src)
        task = doc.activities[0].tasks[0]
        mvp = task.stories_for_release("MVP")
        beta = task.stories_for_release("Beta")
        assert [s.name for s in mvp] == ["Story 1", "Story 3"]
        assert [s.name for s in beta] == ["Story 2"]

    def test_story_without_release_is_unassigned(self):
        src = (
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n"
            "#### Story 1\n"
        )
        doc = StorymapParser().parse(src)
        task = doc.activities[0].tasks[0]
        assert task.stories[0].release() is None
        assert len(task.unassigned_stories()) == 1

    def test_unmatched_release_produces_warning(self):
        src = (
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n"
            "#### Story 1 [release:: NonExistent]\n"
        )
        doc = StorymapParser().parse(src)
        assert any("NonExistent" in w for w in doc.warnings)

    def test_multiple_tasks_independent_release_fields(self):
        src = (
            "# Releases\n## MVP\n## Beta\n\n"
            "# Map\n## A\n"
            "### Task 1\n"
            "#### S1 [release:: MVP]\n"
            "#### S2 [release:: Beta]\n"
            "### Task 2\n"
            "#### S3 [release:: Beta]\n"
        )
        doc = StorymapParser().parse(src)
        t1 = doc.activities[0].tasks[0]
        t2 = doc.activities[0].tasks[1]
        assert len(t1.stories_for_release("MVP")) == 1
        assert len(t1.stories_for_release("Beta")) == 1
        assert len(t2.stories_for_release("Beta")) == 1
        assert len(t2.stories_for_release("MVP")) == 0

    def test_stories_for_release_returns_empty_for_unknown_release(self):
        src = (
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n"
            "#### Story 1 [release:: MVP]\n"
        )
        doc = StorymapParser().parse(src)
        task = doc.activities[0].tasks[0]
        assert task.stories_for_release("Beta") == []

    def test_stories_matched_by_release_id(self):
        src = (
            "# Releases\n## My Very Long Name [id:: mvp]\n\n"
            "# Map\n## A\n### T\n"
            "#### Story 1 [release:: mvp]\n"
        )
        doc = StorymapParser().parse(src)
        task = doc.activities[0].tasks[0]
        assert len(task.stories_for_release("mvp")) == 1
        assert task.stories_for_release("My Very Long Name") == []

    def test_unmatched_release_warns_against_id_not_name(self):
        src = (
            "# Releases\n## Long Name [id:: short]\n\n"
            "# Map\n## A\n### T\n"
            "#### Story 1 [release:: Long Name]\n"
        )
        doc = StorymapParser().parse(src)
        assert any("Long Name" in w for w in doc.warnings)


# ---------------------------------------------------------------------------
# StorymapParser — story fields
# ---------------------------------------------------------------------------


class TestParserStoryFields:
    def test_story_without_fields(self):
        doc = StorymapParser().parse(MINIMAL)
        story = doc.activities[0].tasks[0].stories[0]
        assert story.fields == {}
        assert story.status() == "not-started"

    def test_story_status_field(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].stories[0]
        assert story.fields["status"] == "done"

    def test_story_persona_field(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].stories[0]
        assert story.fields["persona"] == "Margie the Manager"

    def test_story_release_field(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].stories[0]
        assert story.fields["release"] == "MVP"

    def test_story_deadline_field(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].stories[1]
        assert story.fields["deadline"] == "2026-03-01"

    def test_story_with_description(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].stories[0]
        assert "log in with email" in story.description

    def test_story_description_with_link(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].stories[0]
        assert "[issue #1]" in story.description

    def test_story_without_description_is_empty(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].stories[1]
        assert story.description == ""

    def test_story_name_strips_fields(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[0].stories[0]
        assert story.name == "Sign in"
        assert "[status" not in story.name

    def test_blocked_story_with_description(self):
        doc = StorymapParser().parse(FULL)
        story = doc.activities[0].tasks[1].stories[1]
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

    def test_unknown_h1_after_title_is_ignored(self):
        src = (
            "# My Product\n\n"
            "# Introduction\nSome intro text.\n\n"
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert doc.title == "My Product"
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
        story = doc.activities[0].tasks[0].stories[0]
        assert "First paragraph." in story.description
        assert "Second paragraph." in story.description


# ---------------------------------------------------------------------------
# StorymapParser — document title and description
# ---------------------------------------------------------------------------


class TestParserTitle:
    def test_no_title(self):
        doc = StorymapParser().parse(MINIMAL)
        assert doc.title is None

    def test_no_title_description_is_empty(self):
        doc = StorymapParser().parse(MINIMAL)
        assert doc.description == ""

    def test_title_only(self):
        src = (
            "# My Product\n\n"
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert doc.title == "My Product"

    def test_title_with_description(self):
        src = (
            "# My Product\n\n"
            "Short description of the product.\n\n"
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert doc.title == "My Product"
        assert "Short description" in doc.description

    def test_title_description_multiline(self):
        src = (
            "# My Product\n\n"
            "First paragraph.\n\n"
            "Second paragraph.\n\n"
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert "First paragraph." in doc.description
        assert "Second paragraph." in doc.description

    def test_title_description_with_markdown(self):
        src = (
            "# My Product\n\n"
            "**Version:** 1.0 — see [brief](https://docs.example.com)\n\n"
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert "**Version:**" in doc.description
        assert "[brief]" in doc.description

    def test_title_without_description_is_empty_string(self):
        src = (
            "# My Product\n"
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert doc.title == "My Product"
        assert doc.description == ""

    def test_title_does_not_affect_releases(self):
        src = (
            "# My Product\n\n"
            "Some description.\n\n"
            "# Releases\n## MVP\n## Beta\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert len(doc.releases) == 2

    def test_title_does_not_affect_personas(self):
        src = (
            "# My Product\n\n"
            "# Releases\n## MVP\n\n"
            "# Personas\n## Dave\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert len(doc.personas) == 1
        assert doc.personas[0].name == "Dave"

    def test_title_does_not_affect_map(self):
        src = (
            "# My Product\n\n"
            "# Releases\n## MVP\n\n"
            "# Map\n## Activity\n### Task\n#### Story\n"
        )
        doc = StorymapParser().parse(src)
        assert len(doc.activities) == 1
        assert doc.activities[0].tasks[0].stories[0].name == "Story"

    def test_reserved_h1_first_is_not_treated_as_title(self):
        doc = StorymapParser().parse(MINIMAL)
        assert doc.title is None

    def test_title_whitespace_stripped(self):
        src = (
            "#   My Product   \n\n"
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert doc.title == "My Product"


# ---------------------------------------------------------------------------
# StorymapParser — warnings
# ---------------------------------------------------------------------------


class TestParserWarnings:
    def test_no_warnings_for_valid_document(self):
        doc = StorymapParser().parse(FULL)
        assert doc.warnings == []

    def test_unrecognised_h1_produces_warning(self):
        src = (
            "# My Product\n\n"
            "# Introduction\nSome text.\n\n"
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert any("Introduction" in w for w in doc.warnings)

    def test_unrecognised_h1_warning_includes_line_number(self):
        src = (
            "# My Product\n\n"
            "# BadSection\n\n"
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert any("BadSection" in w for w in doc.warnings)
        assert any("Line" in w for w in doc.warnings)

    def test_story_without_task_produces_warning(self):
        src = (
            "# Releases\n## MVP\n\n"
            "# Map\n## Activity\n"
            "#### Orphan story\n"
        )
        doc = StorymapParser().parse(src)
        assert any("Orphan story" in w for w in doc.warnings)
        assert any("no parent task" in w for w in doc.warnings)

    def test_task_without_activity_produces_warning(self):
        src = (
            "# Releases\n## MVP\n\n"
            "# Map\n"
            "### Orphan task\n"
            "#### Story\n"
        )
        doc = StorymapParser().parse(src)
        assert any("Orphan task" in w for w in doc.warnings)
        assert any("no parent activity" in w for w in doc.warnings)

    def test_orphaned_story_not_added_to_document(self):
        src = (
            "# Releases\n## MVP\n\n"
            "# Map\n## Activity\n"
            "#### Orphan story\n"
        )
        doc = StorymapParser().parse(src)
        assert doc.activities[0].tasks == []

    def test_multiple_unrecognised_sections_produce_multiple_warnings(self):
        src = (
            "# Releases\n## MVP\n\n"
            "# Foo\n\n"
            "# Bar\n\n"
            "# Map\n## A\n### T\n#### S\n"
        )
        doc = StorymapParser().parse(src)
        assert sum(1 for w in doc.warnings if "ignored" in w) == 2

    def test_warnings_default_to_empty_list(self):
        doc = StorymapDocument()
        assert doc.warnings == []

    def test_unmatched_release_warning(self):
        src = (
            "# Releases\n## MVP\n\n"
            "# Map\n## A\n### T\n"
            "#### Story 1 [release:: NonExistent]\n"
        )
        doc = StorymapParser().parse(src)
        assert any("NonExistent" in w for w in doc.warnings)
        assert any("not found" in w for w in doc.warnings)
