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
#### Sign in [status:: done] [persona:: Margie the Manager]
User can log in.
---
#### Password reset [status:: in-progress]
### Profile
#### Edit profile
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

    def test_missing_input_exits_nonzero(self, runner):
        result = runner.invoke(main, ["nonexistent.md"])
        assert result.exit_code != 0

    def test_produces_html_output(self, runner, input_file):
        result = runner.invoke(main, [str(input_file)])
        assert result.exit_code == 0
        html_out = input_file.with_suffix(".html")
        assert html_out.exists()

    def test_html_output_is_valid(self, runner, input_file):
        runner.invoke(main, [str(input_file)])
        html = input_file.with_suffix(".html").read_text()
        assert "<!DOCTYPE html>" in html
        assert "User Management" in html

    def test_output_written_to_same_dir_by_default(self, runner, input_file):
        runner.invoke(main, [str(input_file)])
        assert (input_file.parent / "test.html").exists()


# ---------------------------------------------------------------------------
# CLI — output directory
# ---------------------------------------------------------------------------


class TestCliOutputDir:
    def test_custom_output_dir(self, runner, input_file, tmp_path):
        out_dir = tmp_path / "output"
        result = runner.invoke(
            main, [str(input_file), "--output", str(out_dir)]
        )
        assert result.exit_code == 0
        assert (out_dir / "test.html").exists()

    def test_creates_output_dir_if_missing(self, runner, input_file, tmp_path):
        out_dir = tmp_path / "new" / "nested" / "dir"
        result = runner.invoke(
            main, [str(input_file), "--output", str(out_dir)]
        )
        assert result.exit_code == 0
        assert out_dir.exists()

    def test_short_output_flag(self, runner, input_file, tmp_path):
        out_dir = tmp_path / "out"
        result = runner.invoke(main, [str(input_file), "-o", str(out_dir)])
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
            main, [str(input_file), "--template", str(tmpl)]
        )
        assert result.exit_code == 0
        html = input_file.with_suffix(".html").read_text()
        assert "CUSTOM User Management" in html
        assert "<!DOCTYPE html>" not in html

    def test_nonexistent_template_exits_nonzero(self, runner, input_file):
        result = runner.invoke(
            main, [str(input_file), "--template", "nonexistent.html.j2"]
        )
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# CLI — color overrides
# ---------------------------------------------------------------------------


class TestCliColorOverrides:
    def test_status_color_override(self, runner, full_input_file):
        result = runner.invoke(
            main,
            [str(full_input_file), "--status-colors", "done=#00FF00"],
        )
        assert result.exit_code == 0
        html = full_input_file.with_suffix(".html").read_text()
        assert "#00FF00" in html

    def test_ui_color_override(self, runner, full_input_file):
        result = runner.invoke(
            main,
            [str(full_input_file), "--ui-colors", "activity=#ABCDEF"],
        )
        assert result.exit_code == 0
        html = full_input_file.with_suffix(".html").read_text()
        assert "#ABCDEF" in html

    def test_invalid_color_format_exits_nonzero(self, runner, input_file):
        result = runner.invoke(
            main,
            [str(input_file), "--status-colors", "doneBROKEN"],
        )
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# CLI — output messages
# ---------------------------------------------------------------------------


class TestCliOutput:
    def test_parsing_message_shown(self, runner, input_file):
        result = runner.invoke(main, [str(input_file)])
        assert "Parsing" in result.output

    def test_html_success_message_shown(self, runner, input_file):
        result = runner.invoke(main, [str(input_file)])
        assert "HTML" in result.output

    def test_empty_document_warning(self, runner, tmp_path):
        empty = tmp_path / "empty.md"
        empty.write_text("# Not a storymap file\nJust some text.\n")
        result = runner.invoke(main, [str(empty)])
        assert result.exit_code == 0
        assert "Warning" in result.output or "empty" in result.output.lower()
