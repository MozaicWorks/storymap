"""
Command-line interface for storymap.

Usage:
    storymap render input.md
    storymap render input.md --output ./out
    storymap render input.md --template custom.html.j2
    storymap render input.md --status-colors done=#00FF00,blocked=#FF0000
    storymap init
    storymap init myproduct.md

PDF output: open the generated HTML in a browser and use print-to-PDF.
"""

from pathlib import Path

import click
from importlib.metadata import version as pkg_version

from storymap.parser import StorymapParser
from storymap.renderer import StorymapRenderer


_DEFAULT_INIT_FILENAME = "storymap.md"

_SKELETON = """\
<!--
  Storymap format quick reference
  ================================
  # Product Title         — optional, shown at top of output
  # Releases              — define swimlane labels (required)
  # Personas              — UX personas with descriptions (optional)
  # Map                   — the story map itself (required)

  Map hierarchy:
    ## Activity           — column group
    ### Task              — column
    #### Story [key:: val] — card; supported fields:
                             [status:: not-started | in-progress | done | blocked]
                             [persona:: Persona Name]
                             [deadline:: YYYY-MM-DD]

  Use > release on its own line to advance to the next release swimlane.
  You can annotate it for readability — the text after "release" is ignored:
    > release Beta
    > release end of sprint 3
-->

# My Product

Short description of what this product does and who it's for.

# Releases

## MVP

First public release — core functionality only.

## Beta

Invite-only beta with selected users.

# Personas

## Alice the User

- **Role:** End user
- **Tech level:** Medium

Describe Alice's goals, frustrations, and context here.

# Map

## Core Feature

### Main Task

#### First story [status:: done] [persona:: Alice the User]
Describe what this story delivers.

> release Beta

#### Second story [status:: in-progress] [deadline:: 2026-06-01]
Describe what this story delivers.

### Another Task

#### A story [status:: not-started]
"""


def _parse_color_overrides(value: str | None) -> dict[str, str]:
    """
    Parse a comma-separated list of key=value color overrides.

    Example:
        "done=#00FF00,blocked=#FF0000"
        → {"done": "#00FF00", "blocked": "#FF0000"}
    """
    if not value:
        return {}
    result = {}
    for pair in value.split(","):
        pair = pair.strip()
        if "=" not in pair:
            raise click.BadParameter(
                f"Expected key=value, got: {pair!r}. "
                "Example: done=#00FF00,blocked=#FF0000"
            )
        key, color = pair.split("=", 1)
        result[key.strip()] = color.strip()
    return result


def _write_html(html: str, output_path: Path) -> None:
    output_path.write_text(html, encoding="utf-8")
    click.echo(f"  ✓ HTML → {output_path}")


@click.group()
@click.version_option(version=pkg_version("storymap"), prog_name="storymap")
def main() -> None:
    """Generate user story maps from markdown."""


@main.command()
@click.argument(
    "input_file",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
)
@click.option(
    "--output", "-o",
    "output_dir",
    type=click.Path(file_okay=False, writable=True, path_type=Path),
    default=None,
    help="Output directory. Defaults to the same directory as the input file.",
)
@click.option(
    "--template", "-t",
    "template_path",
    type=click.Path(exists=True, dir_okay=False, readable=True, path_type=Path),
    default=None,
    help="Path to a custom Jinja2 HTML template (.html.j2).",
)
@click.option(
    "--status-colors",
    "status_colors_str",
    default=None,
    metavar="KEY=COLOR,...",
    help="Override status colors. Example: done=#00FF00,blocked=#FF0000",
)
@click.option(
    "--ui-colors",
    "ui_colors_str",
    default=None,
    metavar="KEY=COLOR,...",
    help="Override UI colors. Example: activity=#1565C0,task=#90CAF9",
)
def render(
    input_file: Path,
    output_dir: Path | None,
    template_path: Path | None,
    status_colors_str: str | None,
    ui_colors_str: str | None,
) -> None:
    """Render a story map markdown INPUT_FILE to HTML."""

    resolved_output_dir = output_dir or input_file.parent
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    stem = input_file.stem

    try:
        status_colors = _parse_color_overrides(status_colors_str)
        ui_colors = _parse_color_overrides(ui_colors_str)
    except click.BadParameter as e:
        raise click.ClickException(str(e))

    click.echo(f"Parsing {input_file} …")
    try:
        text = input_file.read_text(encoding="utf-8")
        document = StorymapParser().parse(text)
    except Exception as e:
        raise click.ClickException(f"Failed to parse input: {e}")

    if not document.activities and not document.releases:
        click.echo("Warning: document appears empty — no releases or activities found.")

    for warning in document.warnings:
        click.echo(f"  ⚠ {warning}")

    try:
        html = StorymapRenderer().render(
            document,
            template_path=template_path,
            status_colors=status_colors or None,
            ui_colors=ui_colors or None,
        )
    except Exception as e:
        raise click.ClickException(f"Failed to render: {e}")

    _write_html(html, resolved_output_dir / f"{stem}.html")


@main.command()
@click.argument(
    "output_file",
    default=_DEFAULT_INIT_FILENAME,
    type=click.Path(dir_okay=False, path_type=Path),
)
def init(output_file: Path) -> None:
    """Create a skeleton storymap markdown file to get started.

    OUTPUT_FILE defaults to storymap.md in the current directory.
    """
    if output_file.exists():
        raise click.ClickException(
            f"{output_file} already exists. "
            "Choose a different filename or remove the existing file."
        )
    output_file.write_text(_SKELETON, encoding="utf-8")
    click.echo(f"  ✓ Created {output_file}")
    click.echo(f"  Edit it, then run: storymap render {output_file}")
