"""
HTML renderer for storymap documents.

Uses Jinja2 for templating. The default template is bundled at
storymap/templates/default.html.j2. A custom template path can be
provided to render() for minor variations (logo, extra CSS, fonts).

Custom status_colors and ui_colors dicts can be passed to render() to
override the defaults without touching the template.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup
from markdown_it import MarkdownIt

from storymap.model import (
    DEFAULT_STATUS_COLORS,
    DEFAULT_UI_COLORS,
    StorymapDocument,
)

_DEFAULT_TEMPLATE_DIR = Path(__file__).parent / "templates"
_DEFAULT_TEMPLATE_NAME = "default.html.j2"


def _make_render_md() -> tuple:
    """Return (render_md, render_md_intro, render_md_rest) functions."""
    md = MarkdownIt()
    md.disable("lheading")

    def render_md(text: str) -> Markup:
        return Markup(md.render(text))

    def render_md_intro(text: str) -> Markup:
        """Render only the first paragraph of text."""
        intro = text.split("\n\n")[0].strip()
        return Markup(md.render(intro))

    def render_md_rest(text: str) -> Markup:
        """Render everything after the first paragraph, or empty string."""
        parts = text.split("\n\n", 1)
        if len(parts) < 2:
            return Markup("")
        return Markup(md.render(parts[1].strip()))

    return render_md, render_md_intro, render_md_rest


def _darken(hex_color: str, amount: int = 40) -> str:
    """
    Darken a #RRGGBB hex color by subtracting `amount` from each channel.
    Used to produce the story card border-left accent color.
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    r, g, b = (max(0, c - amount) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def _make_jinja_env(template_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # Register darken as a filter so templates can use {{ color | darken }}
    env.filters["darken"] = _darken
    # Register reject_key filter for excluding specific story field keys
    env.filters["reject_key"] = lambda d, key: {
        k: v for k, v in d.items() if k != key
    }
    return env


class StorymapRenderer:
    """Render a StorymapDocument to a self-contained HTML string."""

    def render(
        self,
        document: StorymapDocument,
        template_path: Path | None = None,
        status_colors: dict[str, str] | None = None,
        ui_colors: dict[str, str] | None = None,
    ) -> str:
        """
        Render document to HTML.

        Args:
            document:      The parsed StorymapDocument.
            template_path: Path to a custom .html.j2 template. If None,
                           the bundled default template is used.
            status_colors: Override dict for story status → background color.
                           Merged on top of DEFAULT_STATUS_COLORS.
            ui_colors:     Override dict for structural UI colors.
                           Merged on top of DEFAULT_UI_COLORS.

        Returns:
            A self-contained HTML string.
        """
        resolved_status_colors = {**DEFAULT_STATUS_COLORS, **(status_colors or {})}
        resolved_ui_colors = {**DEFAULT_UI_COLORS, **(ui_colors or {})}

        if template_path is not None:
            template_dir = template_path.parent
            template_name = template_path.name
        else:
            template_dir = _DEFAULT_TEMPLATE_DIR
            template_name = _DEFAULT_TEMPLATE_NAME

        env = _make_jinja_env(template_dir)
        template = env.get_template(template_name)

        # Build a release-index-aware proxy for use inside the template.
        # Jinja2 loop.index0 is scoped to the innermost loop, so we pass
        # the index as a callable context variable instead.
        context = _build_context(document, resolved_status_colors, resolved_ui_colors)

        return template.render(**context)


def _build_context(
    document: StorymapDocument,
    status_colors: dict[str, str],
    ui_colors: dict[str, str],
) -> dict:
    """Build the Jinja2 template context."""
    render_md, render_md_intro, render_md_rest = _make_render_md()
    return {
        "document": document,
        "status_colors": status_colors,
        "ui_colors": ui_colors,
        "render_md": render_md,
        "render_md_intro": render_md_intro,
        "render_md_rest": render_md_rest,
    }
