"""
Command-line interface for storymap.

Usage:
    storymap input.md
    storymap input.md --output ./out
    storymap input.md --template custom.html.j2
    storymap input.md --status-colors done=#00FF00,blocked=#FF0000

PDF output: open the generated HTML in a browser and use print-to-PDF.
"""

import sys
from pathlib import Path

import click

from storymap.parser import StorymapParser
from storymap.renderer import StorymapRenderer


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


@click.command()
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
def main(
    input_file: Path,
    output_dir: Path | None,
    template_path: Path | None,
    status_colors_str: str | None,
    ui_colors_str: str | None,
) -> None:
    """Generate a user story map from a markdown INPUT_FILE."""

    # --- resolve output directory ---
    resolved_output_dir = output_dir or input_file.parent
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    stem = input_file.stem

    # --- parse color overrides ---
    try:
        status_colors = _parse_color_overrides(status_colors_str)
        ui_colors = _parse_color_overrides(ui_colors_str)
    except click.BadParameter as e:
        raise click.ClickException(str(e))

    # --- parse ---
    click.echo(f"Parsing {input_file} …")
    try:
        text = input_file.read_text(encoding="utf-8")
        document = StorymapParser().parse(text)
    except Exception as e:
        raise click.ClickException(f"Failed to parse input: {e}")

    if not document.activities and not document.releases:
        click.echo("Warning: document appears empty — no releases or activities found.")

    # --- render ---
    try:
        html = StorymapRenderer().render(
            document,
            template_path=template_path,
            status_colors=status_colors or None,
            ui_colors=ui_colors or None,
        )
    except Exception as e:
        raise click.ClickException(f"Failed to render: {e}")

    # --- write output ---
    _write_html(html, resolved_output_dir / f"{stem}.html")
