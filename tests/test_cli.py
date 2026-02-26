"""Tests for the storymap CLI."""

import os
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from storymap.cli import _parse_color_overrides, main


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_MARKDOWN = """\
# Releases
## MVP

# Map
## User Management
### Login
#### Sign in
"""

FULL_MARKDOWN = """\
# Releases
## MVP
First public release.

## Beta

# Personas
## Margie the Manager
- **Age:** 45-55

# Map
## User Management
### Authentication
#### Sign in [status:: done] [persona:: Margie the Manager] [release:: MVP]
User can log in.
#### Password reset [status:: in-progress] [release:: Beta]
### Profile
#### Edit profile [release:: MVP]
"""


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def input_file(tmp_path):
    """Write MINIMAL_MARKDOWN to a temp file and return its path."""
    p = tmp_path / "test.md"
    p.write_text(MINIMAL_MARKDOWN, encoding="utf-8")
    return p


@pytest.fixture()
def full_input_file(tmp_path):
    p = tmp_path / "full.md"
    p.write_text(FULL_MARKDOWN, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# _parse_color_overrides (unit)
# ---------------------------------------------------------------------------


class TestParseColorOverrides:
    def test_empty_string_returns_empty_dict(self):
        assert _parse_color_overrides("") == {}

    def test_none_returns_empty_dict(self):
        assert _parse_color_overrides(None) == {}

    def test_single_pair(self):
        assert _parse_color_overrides("done=#00FF00") == {"done": "#00FF00"}

    def test_multiple_pairs(self):
        result = _parse_color_overrides("done=#00FF00,blocked=#FF0000")
        assert result == {"done": "#00FF00", "blocked": "#FF0000"}

    def test_strips_whitespace(self):
        result = _parse_color_overrides(" done = #00FF00 , blocked = #FF0000 ")
        assert result == {"done": "#00FF00", "blocked": "#FF0000"}

    def test_invalid_pair_raises(self):
        import click
        with pytest.raises(click.BadParameter):
            _parse_color_overrides("done#00FF00")

    def test_value_with_hash(self):
        result = _parse_color_overrides("activity=#1565C0")
        assert result == {"activity": "#1565C0"}


# ---------------------------------------------------------------------------
# CLI — basic invocation
# ---------------------------------------------------------------------------


class TestCliBasic:
    def test_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "INPUT_FILE" in result.output

    def test_version_flag(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "storymap" in result.output
        assert "." in result.output  # version number contains a dot

    def test_missing_input_exits_nonzero(self, runner):
        result = runner.invoke(main, ["render", "nonexistent.md"])
        assert result.exit_code != 0

    def test_produces_html_output(self, runner, input_file):
        result = runner.invoke(main, ["render", str(input_file)])
        assert result.exit_code == 0
        html_out = input_file.with_suffix(".html")
        assert html_out.exists()

    def test_html_output_is_valid(self, runner, input_file):
        runner.invoke(main, ["render", str(input_file)])
        html = input_file.with_suffix(".html").read_text()
        assert "<!DOCTYPE html>" in html
        assert "User Management" in html

    def test_output_written_to_same_dir_by_default(self, runner, input_file):
        runner.invoke(main, ["render", str(input_file)])
        assert (input_file.parent / "test.html").exists()


# ---------------------------------------------------------------------------
# CLI — output directory
# ---------------------------------------------------------------------------


class TestCliOutputDir:
    def test_custom_output_dir(self, runner, input_file, tmp_path):
        out_dir = tmp_path / "output"
        result = runner.invoke(
            main, ["render", str(input_file), "--output", str(out_dir)]
        )
        assert result.exit_code == 0
        assert (out_dir / "test.html").exists()

    def test_creates_output_dir_if_missing(self, runner, input_file, tmp_path):
        out_dir = tmp_path / "new" / "nested" / "dir"
        result = runner.invoke(
            main, ["render", str(input_file), "--output", str(out_dir)]
        )
        assert result.exit_code == 0
        assert out_dir.exists()

    def test_short_output_flag(self, runner, input_file, tmp_path):
        out_dir = tmp_path / "out"
        result = runner.invoke(main, ["render", str(input_file), "-o", str(out_dir)])
        assert result.exit_code == 0
        assert (out_dir / "test.html").exists()


# ---------------------------------------------------------------------------
# CLI — custom template
# ---------------------------------------------------------------------------


class TestCliCustomTemplate:
    def test_custom_template_used(self, runner, input_file, tmp_path):
        tmpl = tmp_path / "custom.html.j2"
        tmpl.write_text(
            "<html><body>CUSTOM {{ document.activities[0].name }}</body></html>"
        )
        result = runner.invoke(
            main, ["render", str(input_file), "--template", str(tmpl)]
        )
        assert result.exit_code == 0
        html = input_file.with_suffix(".html").read_text()
        assert "CUSTOM User Management" in html
        assert "<!DOCTYPE html>" not in html

    def test_nonexistent_template_exits_nonzero(self, runner, input_file):
        result = runner.invoke(
            main, ["render", str(input_file), "--template", "nonexistent.html.j2"]
        )
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# CLI — color overrides
# ---------------------------------------------------------------------------


class TestCliColorOverrides:
    def test_status_color_override(self, runner, full_input_file):
        result = runner.invoke(
            main,
            ["render", str(full_input_file), "--status-colors", "done=#00FF00"],
        )
        assert result.exit_code == 0
        html = full_input_file.with_suffix(".html").read_text()
        assert "#00FF00" in html

    def test_ui_color_override(self, runner, full_input_file):
        result = runner.invoke(
            main,
            ["render", str(full_input_file), "--ui-colors", "activity=#ABCDEF"],
        )
        assert result.exit_code == 0
        html = full_input_file.with_suffix(".html").read_text()
        assert "#ABCDEF" in html

    def test_invalid_color_format_exits_nonzero(self, runner, input_file):
        result = runner.invoke(
            main,
            ["render", str(input_file), "--status-colors", "doneBROKEN"],
        )
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# CLI — output messages
# ---------------------------------------------------------------------------


class TestCliOutput:
    def test_parsing_message_shown(self, runner, input_file):
        result = runner.invoke(main, ["render", str(input_file)])
        assert "Parsing" in result.output

    def test_html_success_message_shown(self, runner, input_file):
        result = runner.invoke(main, ["render", str(input_file)])
        assert "HTML" in result.output

    def test_empty_document_warning(self, runner, tmp_path):
        empty = tmp_path / "empty.md"
        empty.write_text("# Not a storymap file\nJust some text.\n")
        result = runner.invoke(main, ["render", str(empty)])
        assert result.exit_code == 0
        assert "Warning" in result.output or "empty" in result.output.lower()


# ---------------------------------------------------------------------------
# CLI — init subcommand
# ---------------------------------------------------------------------------


class TestCliInit:
    def test_creates_default_file(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 0
            assert Path("storymap.md").exists()

    def test_default_file_contains_skeleton(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(main, ["init"])
            content = Path("storymap.md").read_text()
            assert "# Releases" in content
            assert "# Map" in content
            assert "release::" in content

    def test_default_file_contains_format_comment(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(main, ["init"])
            content = Path("storymap.md").read_text()
            assert "release::" in content

    def test_creates_named_file(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init", "myproduct.md"])
            assert result.exit_code == 0
            assert Path("myproduct.md").exists()

    def test_refuses_to_overwrite_existing_file(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("storymap.md").write_text("existing content")
            result = runner.invoke(main, ["init"])
            assert result.exit_code != 0
            assert Path("storymap.md").read_text() == "existing content"

    def test_success_message_shown(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])
            assert "storymap.md" in result.output

    def test_next_step_hint_shown(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])
            assert "render" in result.output

    def test_skeleton_is_valid_storymap(self, runner, tmp_path):
        """The skeleton produced by init should parse without warnings."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            runner.invoke(main, ["init"])
            from storymap.parser import StorymapParser
            content = Path("storymap.md").read_text()
            doc = StorymapParser().parse(content)
            assert doc.warnings == []
            assert len(doc.releases) >= 1
            assert len(doc.activities) >= 1
