# storymap

Generate user story maps from markdown. Write your product spec as a readable
document — personas, releases, activities, tasks, and stories — and render it
as a styled HTML page or PDF.

## Installation

```bash
pip install storymap
```

For PDF output, also install [weasyprint](https://weasyprint.org/):

```bash
pip install weasyprint
```

## Quick start

```bash
storymap mymap.md                   # → mymap.html (same directory)
storymap mymap.md --format pdf      # → mymap.pdf
storymap mymap.md --format both     # → mymap.html + mymap.pdf
storymap mymap.md -o ./output       # → output/mymap.html
```

## Document format

A storymap file is a standard markdown document with four reserved top-level
sections: `Releases`, `Personas`, `Map`, and optionally any other headings
you want (they are ignored by the renderer but appear in the PDF).

```markdown
# Releases
## MVP
First public release targeting core authentication.

## Beta
Invite-only beta with selected users.

# Personas
## Margie the Manager
- **Age:** 45–55
- **Location:** Suburban midwest
- **Job title:** Operations Manager
- **Tech level:** Low — uses email and Excel, avoids new tools

Margie manages a team of 8 and primarily accesses the app on her phone.

![Margie](margie.jpg){width=200px}

[Research interview notes](https://docs.google.com/...)

## Dave the Developer
- **Age:** 28–35
- **Tech level:** High — API-first mindset

# Map
## User Management
### Authentication
#### Sign in [status:: done] [persona:: Margie the Manager]
User can log in with email and password.
See [issue #1](https://github.com/org/repo/issues/1)
---
#### Password reset [status:: in-progress] [deadline:: 2026-03-01]

### Profile
#### Edit profile [status:: done]
---
#### Upload avatar [status:: blocked]
Blocked pending storage provider decision.

## Reporting
### Dashboard
#### View summary [status:: not-started] [persona:: Margie the Manager]
---
#### Export to CSV [deadline:: 2026-06-01]
```

### Sections

| Section | Required | Purpose |
|---|---|---|
| `# Releases` | Yes | Defines release swimlanes |
| `# Personas` | No | UX persona descriptions |
| `# Map` | Yes | The story map itself |

Section names are case-insensitive. Any other `#` headings are passed through
to the rendered output unchanged, allowing you to add an introduction,
project goals, or other context that makes the PDF self-contained.

### Map hierarchy

```
## Activity       (column group)
### Task          (column)
#### Story        (card in a swimlane)
```

Stories are grouped into release swimlanes by `---` separators within each
task. Stories before the first `---` belong to the first release, after the
first `---` to the second release, and so on.

```markdown
### Authentication
#### Sign in          ← Release 1 (MVP)
#### Remember me      ← Release 1 (MVP)
---
#### SSO              ← Release 2 (Beta)
---
                      ← Release 3 empty for this task
```

### Story fields

Stories support optional inline fields using the
[Dataview](https://blacksmithgu.github.io/obsidian-dataview/) `[key:: value]`
syntax. Fields appear as badges on the rendered story card.

```markdown
#### Story name [status:: done] [persona:: Margie the Manager] [deadline:: 2026-03-01]
```

| Field | Values | Default |
|---|---|---|
| `status` | `not-started`, `in-progress`, `done`, `blocked` | `not-started` |
| `persona` | Any string matching a persona name | — |
| `deadline` | ISO date `YYYY-MM-DD` | — |

Any other `[key:: value]` field is accepted and rendered as a badge, making
the format forward-compatible with future additions.

### Story descriptions

Markdown content following a `#### Story` heading and before the next
heading or `---` separator is treated as the story description. Descriptions
support standard markdown: bold, italics, links, lists.

```markdown
#### Sign in [status:: done]
User can log in with email and password.
See [issue #1](https://github.com/org/repo/issues/1)
```

> **Note:** Do not use `---` inside story descriptions — it will be
> interpreted as a release boundary. Use `***` or `___` for a horizontal
> rule in descriptions if needed (these are parsed as thematic breaks by
> markdown but do not trigger release advancement in storymap).

## CLI reference

```
Usage: storymap [OPTIONS] INPUT_FILE

  Generate a user story map from a markdown INPUT_FILE.

Options:
  -f, --format [html|pdf|both]    Output format.  [default: html]
  -o, --output DIR                Output directory. Defaults to the input
                                  file's directory.
  -t, --template FILE             Path to a custom Jinja2 template (.html.j2).
  --status-colors KEY=COLOR,...   Override status colors.
                                  Example: done=#00FF00,blocked=#FF0000
  --ui-colors KEY=COLOR,...       Override UI colors.
                                  Example: activity=#1565C0,task=#90CAF9
  --help                          Show this message and exit.
```

## Customisation

### Color overrides

Override any status or UI color from the command line:

```bash
storymap mymap.md \
  --status-colors "done=#27AE60,in-progress=#2980B9,blocked=#E74C3C" \
  --ui-colors "activity=#2C3E50,task=#34495E"
```

Default status colors:

| Status | Color |
|---|---|
| `not-started` | `#E0E0E0` grey |
| `in-progress` | `#90CAF9` blue |
| `done` | `#A5D6A7` green |
| `blocked` | `#EF9A9A` red |

### Custom templates

Copy the bundled template and modify it:

```bash
# find the bundled template
python -c "import storymap; print(storymap.__file__)"
# → /path/to/storymap/__init__.py
# template is at /path/to/storymap/templates/default.html.j2
```

Then render with your custom template:

```bash
storymap mymap.md --template my-template.html.j2
```

The template receives the following context variables:

| Variable | Type | Description |
|---|---|---|
| `document` | `StorymapDocument` | The full parsed document |
| `status_colors` | `dict[str, str]` | Resolved status → hex color |
| `ui_colors` | `dict[str, str]` | Resolved UI element → hex color |
| `render_md` | `callable` | Render a markdown string to HTML |

The `darken` filter is also available: `{{ color | darken }}`.

## Development

```bash
git clone https://github.com/yourorg/storymap
cd storymap
pip install -e ".[dev]"
pytest
```

### Project structure

```
storymap/
├── model.py       — dataclasses and default color constants
├── parser.py      — markdown-it-py state machine parser
├── renderer.py    — Jinja2 HTML renderer
├── cli.py         — click CLI entry point
└── templates/
    └── default.html.j2
tests/
├── test_model.py
├── test_parser.py
├── test_renderer.py
└── test_cli.py
```

## License

MIT
