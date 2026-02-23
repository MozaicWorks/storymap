# storymap

Generate user story maps from markdown. Write your product spec as a readable
document — personas, releases, activities, tasks, and stories — and render it
as a styled HTML page or PDF.

## Installation

Requires [pipenv](https://pipenv.pypa.io) and [just](https://github.com/casey/just).

```bash
git clone https://github.com/yourorg/storymap
cd storymap
just install
```

## Quick start

```bash
storymap init                   # → storymap.md in current directory
storymap init myproduct.md      # → myproduct.md
just run mymap.md               # → out/mymap.html
just run-out mymap.md ./output  # → output/mymap.html
```

Or directly via pipenv:

```bash
pipenv run storymap render mymap.md --output ./out
```

**PDF output:** open the generated HTML in a browser and use print-to-PDF
(Ctrl+P → Save as PDF). Browser print produces better results than any
automated converter for wide table layouts.

## Just commands

| Command | Description |
|---|---|
| `just install` | Install dependencies and package in editable mode |
| `just init` | Create a skeleton storymap.md in current directory |
| `just init-named FILE` | Create a skeleton with a specific filename |
| `just run FILE` | Render HTML output from a markdown file (→ out/) |
| `just run-out FILE DIR` | Render HTML output to a specific directory |
| `just test` | Run all tests |
| `just test-v` | Run all tests with verbose output |
| `just test-module MODULE` | Run tests for one module (e.g. `just test-module parser`) |
| `just template-path` | Print the path to the bundled default template |
| `just clean` | Remove the out/ folder |
| `just clean-build` | Remove build artifacts including egg-info |
| `just clean-env` | Remove the virtualenv and lock file |
| `just build` | Build distribution packages (sdist + wheel) |
| `just publish` | Upload to PyPI |
| `just publish-test` | Upload to TestPyPI for a dry run |
| `just release` | Tag, push, and create a GitHub release |

## Document format

A storymap file is a standard markdown document with four reserved top-level
sections: `Releases`, `Personas`, `Map`, and optionally any other headings
you want (they are ignored by the renderer but appear in the HTML output).

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

Stories are grouped into release swimlanes by `> release` separators within each
task. Stories before the first `> release` belong to the first release, after the
first `> release` to the second release, and so on.

```markdown
### Authentication
#### Sign in          ← Release 1 (MVP)
#### Remember me      ← Release 1 (MVP)
> release
#### SSO              ← Release 2 (Beta)
> release
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
just template-path
# → /path/to/storymap/templates/default.html.j2
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

## Known limitations

There are no known format limitations at this time.

## Development

```bash
git clone https://github.com/yourorg/storymap
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
