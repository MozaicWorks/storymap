# storymap

Generate user story maps from markdown. Write your product spec as a readable
document — personas, releases, activities, tasks, and stories — and render it
as a styled HTML page.

## Installation

```bash
pip install storymap
```

## Quick start

```bash
storymap init                   # create a skeleton storymap.md
storymap init myproduct.md      # create a named skeleton
storymap render mymap.md        # → mymap.html (same directory)
storymap render mymap.md -o out # → out/mymap.html
```

**PDF output:** open the generated HTML in a browser and use print-to-PDF
(Ctrl+P → Save as PDF). The HTML includes print-optimised CSS for landscape
layout and color preservation.

## Document format

A storymap file is a standard markdown document with three reserved top-level
sections: `# Releases`, `# Personas`, and `# Map`. Any other `#` heading is
treated as the document title (first one) or passed through to the output.

```markdown
# My Product
Short description.

# Releases
## MVP
First public release.

## Beta
Invite-only beta with selected users.

# Personas
## Margie the Manager
- **Age:** 45–55
- **Tech level:** Low

Margie manages a team of 8 and primarily uses the app on mobile.

# Map
## User Management
### Authentication
#### Sign in [status:: done] [persona:: Margie the Manager]
User can log in with email and password.

> release Beta

#### Password reset [status:: in-progress] [deadline:: 2026-03-01]

### Profile
#### Edit profile [status:: done]

> release Beta

#### Upload avatar [status:: blocked]
Blocked pending storage provider decision.
```

### Sections

| Section | Required | Purpose |
|---|---|---|
| `# Releases` | Yes | Defines release swimlanes |
| `# Personas` | No | UX persona descriptions |
| `# Map` | Yes | The story map itself |

Section names are case-insensitive.

### Map hierarchy

```
## Activity       (column group)
### Task          (column)
#### Story        (card in a swimlane)
```

Use `> release` on its own line to advance to the next release swimlane within
a task. Annotate it for readability — anything after `release` is ignored:

```markdown
### Authentication
#### Sign in          ← Release 1 (MVP)
#### Remember me      ← Release 1 (MVP)
> release Beta
#### SSO              ← Release 2 (Beta)
> release GA
                      ← Release 3 empty for this task
```

Keep `> release` count consistent across all tasks — mismatched counts produce
misaligned swimlane rows.

### Story fields

Stories support optional inline fields using `[key:: value]` syntax.
Fields appear as badges on the rendered story card.

```markdown
#### Story name [status:: done] [persona:: Margie the Manager] [deadline:: 2026-03-01]
```

| Field | Values | Default |
|---|---|---|
| `status` | `not-started`, `in-progress`, `done`, `blocked` | `not-started` |
| `persona` | Any string matching a persona name | — |
| `deadline` | ISO date `YYYY-MM-DD` | — |

Any other `[key:: value]` field is accepted and rendered as a badge.

### Story descriptions

Markdown content following a `#### Story` heading and before the next heading
or `> release` separator is treated as the story description. Descriptions
support standard markdown: bold, italics, links, lists.

## CLI reference

```
Usage: storymap [OPTIONS] COMMAND [ARGS]...

  Generate user story maps from markdown.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  init    Create a skeleton storymap markdown file to get started.
  render  Render a story map markdown INPUT_FILE to HTML.
```

### storymap render

```
Usage: storymap render [OPTIONS] INPUT_FILE

Options:
  -o, --output DIR                Output directory. Defaults to the input
                                  file's directory.
  -t, --template FILE             Path to a custom Jinja2 template (.html.j2).
  --status-colors KEY=COLOR,...   Override status colors.
                                  Example: done=#00FF00,blocked=#FF0000
  --ui-colors KEY=COLOR,...       Override UI colors.
                                  Example: activity=#1565C0,task=#90CAF9
  --help                          Show this message and exit.
```

### storymap init

```
Usage: storymap init [OUTPUT_FILE]

  OUTPUT_FILE defaults to storymap.md in the current directory.
  Refuses to overwrite an existing file.
```

## Customisation

### Color overrides

```bash
storymap render mymap.md \
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

```bash
storymap render mymap.md --template my-template.html.j2
```

The template receives:

| Variable | Type | Description |
|---|---|---|
| `document` | `StorymapDocument` | The full parsed document |
| `status_colors` | `dict[str, str]` | Resolved status → hex color |
| `ui_colors` | `dict[str, str]` | Resolved UI element → hex color |
| `render_md` | `callable` | Render a markdown string to HTML |

The `darken` filter is also available: `{{ color | darken }}`.

## Development

Requires [pipenv](https://pipenv.pypa.io) and [just](https://github.com/casey/just).

```bash
git clone https://github.com/mozaicworks/storymap
cd storymap
just install
just test
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
