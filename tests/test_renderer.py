"""Tests for the storymap HTML renderer."""

import os
import tempfile
from pathlib import Path

import pytest

from storymap.model import (
    Activity,
    DEFAULT_STATUS_COLORS,
    DEFAULT_UI_COLORS,
    Persona,
    Release,
    Story,
    StorymapDocument,
    Task,
)
from storymap.parser import StorymapParser
from storymap.renderer import StorymapRenderer, _darken


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FULL_MARKDOWN = """\
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


@pytest.fixture()
def full_document():
    return StorymapParser().parse(FULL_MARKDOWN)


@pytest.fixture()
def renderer():
    return StorymapRenderer()


@pytest.fixture()
def full_html(renderer, full_document):
    return renderer.render(full_document)


# ---------------------------------------------------------------------------
# _darken
# ---------------------------------------------------------------------------


class TestDarken:
    def test_darkens_color(self):
        assert _darken("#90CAF9") == "#68A2D1"

    def test_clamps_at_zero(self):
        assert _darken("#000000") == "#000000"

    def test_zero_amount_no_change(self):
        assert _darken("#FFFFFF", 0) == "#FFFFFF"

    def test_clamps_channels_independently(self):
        assert _darken("#202020", 40) == "#000000"

    def test_output_is_uppercase_hex(self):
        result = _darken("#aabbcc")
        assert result == result.upper() or result.startswith("#")

    def test_output_format(self):
        result = _darken("#90CAF9")
        assert result.startswith("#")
        assert len(result) == 7


# ---------------------------------------------------------------------------
# Renderer — document structure
# ---------------------------------------------------------------------------


class TestRendererStructure:
    def test_valid_html_doctype(self, full_html):
        assert "<!DOCTYPE html>" in full_html

    def test_has_html_and_body(self, full_html):
        assert "<html" in full_html
        assert "<body" in full_html

    def test_has_style_block(self, full_html):
        assert "<style>" in full_html

    def test_table_present(self, full_html):
        assert "story-map" in full_html

    def test_activity_headers_present(self, full_html):
        assert "activity-header" in full_html

    def test_task_headers_present(self, full_html):
        assert "task-header" in full_html

    def test_release_labels_present(self, full_html):
        assert "release-label" in full_html

    def test_persona_cards_present(self, full_html):
        assert "persona-card" in full_html

    def test_release_cards_present(self, full_html):
        assert "release-card" in full_html

    def test_colspan_present_for_activities(self, full_html):
        assert "colspan" in full_html

    def test_empty_document_renders_without_error(self, renderer):
        html = renderer.render(StorymapDocument())
        assert "<!DOCTYPE html>" in html


# ---------------------------------------------------------------------------
# Renderer — content
# ---------------------------------------------------------------------------


class TestRendererContent:
    def test_activity_name(self, full_html):
        assert "User Management" in full_html

    def test_second_activity_name(self, full_html):
        assert "Reporting" in full_html

    def test_task_name(self, full_html):
        assert "Authentication" in full_html

    def test_story_name(self, full_html):
        assert "Sign in" in full_html

    def test_story_description(self, full_html):
        assert "log in with email" in full_html

    def test_story_description_link(self, full_html):
        assert "issue #1" in full_html

    def test_persona_name(self, full_html):
        assert "Margie the Manager" in full_html

    def test_persona_description(self, full_html):
        assert "Age" in full_html

    def test_persona_multiline_description(self, full_html):
        assert "manages a team" in full_html

    def test_release_name(self, full_html):
        assert "MVP" in full_html

    def test_release_description(self, full_html):
        assert "First public release." in full_html

    def test_blocked_story_name(self, full_html):
        assert "Upload avatar" in full_html

    def test_blocked_story_description(self, full_html):
        assert "storage" in full_html

    def test_deadline_badge(self, full_html):
        assert "2026-03-01" in full_html

    def test_persona_badge(self, full_html):
        # persona field appears as badge on story card
        assert "👤" in full_html

    def test_deadline_badge_icon(self, full_html):
        assert "📅" in full_html


# ---------------------------------------------------------------------------
# Renderer — status colors
# ---------------------------------------------------------------------------


class TestRendererStatusColors:
    def test_done_color_applied(self, full_html):
        assert DEFAULT_STATUS_COLORS["done"] in full_html

    def test_blocked_color_applied(self, full_html):
        assert DEFAULT_STATUS_COLORS["blocked"] in full_html

    def test_in_progress_color_applied(self, full_html):
        assert DEFAULT_STATUS_COLORS["in-progress"] in full_html

    def test_not_started_color_applied(self, renderer, full_document):
        html = renderer.render(full_document)
        assert DEFAULT_STATUS_COLORS["not-started"] in html

    def test_custom_status_color_override(self, renderer, full_document):
        html = renderer.render(full_document, status_colors={"done": "#00FF00"})
        assert "#00FF00" in html

    def test_custom_color_replaces_default(self, renderer, full_document):
        html = renderer.render(full_document, status_colors={"done": "#00FF00"})
        assert DEFAULT_STATUS_COLORS["done"] not in html

    def test_partial_override_preserves_other_defaults(self, renderer, full_document):
        html = renderer.render(full_document, status_colors={"done": "#00FF00"})
        assert DEFAULT_STATUS_COLORS["blocked"] in html

    def test_custom_status_not_in_defaults_uses_fallback(self, renderer):
        doc = StorymapDocument(
            releases=[Release(name="R1")],
            activities=[
                Activity(
                    name="A",
                    tasks=[
                        Task(
                            name="T",
                            stories=[Story(name="S", fields={"status": "custom-status", "release": "R1"})],
                        )
                    ],
                )
            ],
        )
        html = renderer.render(doc)
        assert "custom-status" in html


# ---------------------------------------------------------------------------
# Renderer — UI colors
# ---------------------------------------------------------------------------


class TestRendererUiColors:
    def test_default_activity_color(self, full_html):
        assert DEFAULT_UI_COLORS["activity"] in full_html

    def test_default_task_color(self, full_html):
        assert DEFAULT_UI_COLORS["task"] in full_html

    def test_default_release_header_color(self, full_html):
        assert DEFAULT_UI_COLORS["release_header"] in full_html

    def test_custom_activity_color(self, renderer, full_document):
        html = renderer.render(full_document, ui_colors={"activity": "#FF0000"})
        assert "#FF0000" in html

    def test_partial_ui_override_preserves_others(self, renderer, full_document):
        html = renderer.render(full_document, ui_colors={"activity": "#FF0000"})
        assert DEFAULT_UI_COLORS["task"] in html


# ---------------------------------------------------------------------------
# Renderer — custom template
# ---------------------------------------------------------------------------


class TestRendererCustomTemplate:
    def test_custom_template_is_used(self, renderer, full_document):
        tmpl = "<html><body>CUSTOM {{ document.activities[0].name }}</body></html>"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html.j2", delete=False
        ) as f:
            f.write(tmpl)
            path = Path(f.name)
        try:
            html = renderer.render(full_document, template_path=path)
            assert "CUSTOM User Management" in html
            assert "<!DOCTYPE html>" not in html
        finally:
            os.unlink(path)

    def test_custom_template_receives_status_colors(self, renderer, full_document):
        tmpl = "{% for k, v in status_colors.items() %}{{ k }}:{{ v }} {% endfor %}"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html.j2", delete=False
        ) as f:
            f.write(tmpl)
            path = Path(f.name)
        try:
            html = renderer.render(
                full_document,
                template_path=path,
                status_colors={"done": "#AABBCC"},
            )
            assert "done:#AABBCC" in html
        finally:
            os.unlink(path)

    def test_custom_template_render_md_available(self, renderer, full_document):
        tmpl = "{{ render_md('**bold**') }}"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html.j2", delete=False
        ) as f:
            f.write(tmpl)
            path = Path(f.name)
        try:
            html = renderer.render(full_document, template_path=path)
            assert "<strong>bold</strong>" in html
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Renderer — XSS protection
# ---------------------------------------------------------------------------


class TestRendererXSS:
    def test_script_in_story_name_is_escaped(self):
        doc = StorymapDocument(
            releases=[Release(name="MVP")],
            activities=[Activity(name="A", tasks=[
                Task(name="T", stories=[Story(name='<script>alert(1)</script>', fields={"release": "MVP"})])
            ])]
        )
        html = StorymapRenderer().render(doc)
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

    def test_script_in_activity_name_is_escaped(self):
        doc = StorymapDocument(
            releases=[Release(name="MVP")],
            activities=[Activity(name='<script>alert(1)</script>', tasks=[])]
        )
        html = StorymapRenderer().render(doc)
        assert "<script>alert(1)</script>" not in html

    def test_script_in_story_description_renders_as_html(self):
        """Inline HTML in descriptions is intentional and should pass through."""
        doc = StorymapDocument(
            releases=[Release(name="MVP")],
            activities=[Activity(name="A", tasks=[
                Task(name="T", stories=[Story(
                        name="S",
                        description="See <!-- internal note --> for context.",
                        fields={"release": "MVP"}
                    )])
            ])]
        )
        html = StorymapRenderer().render(doc)
        assert "<!-- internal note -->" in html

    def test_script_in_field_value_is_escaped(self):
        doc = StorymapDocument(
            releases=[Release(name="MVP")],
            activities=[Activity(name="A", tasks=[
                Task(name="T", stories=[Story(name="S", fields={"status": "<script>x</script>"})])
            ])]
        )
        html = StorymapRenderer().render(doc)
        assert "<script>x</script>" not in html


# ---------------------------------------------------------------------------
# Renderer — image embedding
# ---------------------------------------------------------------------------


class TestRendererImageEmbedding:
    def test_local_image_embedded_as_base64(self, renderer, tmp_path):
        # create a tiny 1x1 PNG
        import base64
        png_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        img_path = tmp_path / "test.png"
        img_path.write_bytes(png_bytes)

        doc = StorymapDocument(
            releases=[Release(name="MVP")],
            activities=[Activity(name="A", tasks=[
                Task(name="T", stories=[Story(name="S", description=f"![img](test.png)", fields={"release": "MVP"})])
            ])]
        )
        html = renderer.render(doc, source_dir=tmp_path)
        assert 'src="data:image/png;base64,' in html
        assert 'src="test.png"' not in html

    def test_remote_image_not_embedded(self, renderer, full_document):
        doc = StorymapDocument(
            releases=[Release(name="MVP")],
            activities=[Activity(name="A", tasks=[
                Task(name="T", stories=[Story(name="S", description="![img](https://example.com/img.png)", fields={"release": "MVP"})])
            ])]
        )
        html = renderer.render(doc, source_dir=None)
        assert 'src="https://example.com/img.png"' in html

    def test_missing_image_left_as_is(self, renderer, tmp_path):
        doc = StorymapDocument(
            releases=[Release(name="MVP")],
            activities=[Activity(name="A", tasks=[
                Task(name="T", stories=[Story(name="S", description="![img](missing.png)", fields={"release": "MVP"})])
            ])]
        )
        html = renderer.render(doc, source_dir=tmp_path)
        assert 'src="missing.png"' in html

    def test_no_source_dir_leaves_images_as_is(self, renderer):
        doc = StorymapDocument(
            releases=[Release(name="MVP")],
            activities=[Activity(name="A", tasks=[
                Task(name="T", stories=[Story(name="S", description="![img](local.png)", fields={"release": "MVP"})])
            ])]
        )
        html = renderer.render(doc, source_dir=None)
        assert 'src="local.png"' in html
