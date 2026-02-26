# storymap

Generate user story maps from markdown. Write your product spec as a readable
document — personas, releases, activities, tasks, and stories — and render it
as a styled, interactive HTML page.

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

The output is a single self-contained HTML file. Local images referenced in
story descriptions are embedded as base64 data URIs — no external files needed.

**PDF output:** open the generated HTML in a browser and use print-to-PDF
(Ctrl+P → Save as PDF). The HTML includes print-optimised CSS for landscape
layout and color preservation.

## Document format

A storymap file is a standard markdown document with three reserved top-level
sections: `# Releases`, `# Personas`, and `# Map`. Any other `#` heading is
treated as the document title (first one) or ignored.

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
#### Sign in [status:: done] [persona:: Margie the Manager] [release:: MVP]
User can log in with email and password.

#### Password reset [status:: in-progress] [deadline:: 2026-03-01] [release:: Beta]

### Profile
#### Edit profile [status:: done] [release:: MVP]

#### Upload avatar [status:: blocked] [release:: Beta]
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

### Assigning stories to releases

Use the `[release:: name]` field on each story to assign it to a release
swimlane. The name must match a release defined in the `# Releases` section.
Stories without a `[release::]` field are parsed but not shown in any swimlane.

```markdown
### Authentication
#### Sign in [status:: done] [release:: MVP]
#### Remember me [status:: done] [release:: MVP]
#### SSO [status:: not-started] [release:: Beta]
#### SAML [status:: not-started] [release:: GA]
```

This is more explicit than positional separators — each story carries its own
release assignment regardless of order in the file.

### Story fields

Stories support optional inline fields using `[key:: value]` syntax.
Fields appear as badges on the rendered story card.

```markdown
#### Story name [status:: done] [persona:: Margie the Manager] [deadline:: 2026-03-01] [release:: MVP]
```

| Field | Values | Default |
|---|---|---|
| `status` | `not-started`, `in-progress`, `done`, `blocked` | `not-started` |
| `release` | Release name from `# Releases` section | — |
| `persona` | Any string matching a persona name | — |
| `deadline` | ISO date `YYYY-MM-DD` | — |

Any other `[key:: value]` field is accepted and rendered as a badge.

### Story descriptions

Markdown content following a `#### Story` heading and before the next heading
is treated as the story description. Descriptions support standard markdown:
bold, italics, links, lists, and images.

The first paragraph is always visible on the story card. Additional paragraphs
(separated by a blank line) are shown only in Detail zoom level.

```markdown
#### Sign in [status:: done] [release:: MVP]
User can log in with email and password.

**Acceptance criteria:**
- Given valid credentials, user is redirected to dashboard
- Given invalid credentials, an error message is shown

![wireframe](./screens/sign-in.png)
```

### Images

Images in story descriptions and persona descriptions are embedded as base64
data URIs in the output HTML, making the file fully self-contained. Paths are
resolved relative to the source `.md` file. Remote URLs are left as-is.

## Interactive HTML features

The rendered HTML includes controls for navigating large maps:

**Zoom levels** — three buttons in the sticky header:
- **Overview** — story names only, compact layout
- **Map** — story names, status badges, and first-paragraph descriptions
- **Detail** — full descriptions and acceptance criteria expanded

**Release focus** — a dropdown to highlight one release swimlane and dim
the rest. Works independently of the zoom level.

**Story Lens** — a toggle that enables click-to-zoom on individual story cards.
When active, clicking a card expands it to ~40% of the viewport width with full
details visible. Clicking outside collapses it. Stories in the focused release
(if any) are the only ones that can be expanded.

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
| `render_md_intro` | `callable` | Render first paragraph only |
| `render_md_rest` | `callable` | Render everything after first paragraph |

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
├── renderer.py    — Jinja2 HTML renderer with base64 image embedding
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
