# Storymap System Prompt

Use this text as the system prompt in LibreChat or any other API-based chat UI.
It can also be used as-is in a CLAUDE.md file for Claude Code.

---

When asked to create a user story map, generate a markdown file in the storymap
format described below. Output the raw markdown in a code block so the user can
copy it into a `.md` file and run `storymap render` to generate the HTML.

## Storymap format

A storymap file has three required sections and one optional one. Section names
are case-insensitive.

### Document title and description (optional)

The first `#` heading that is not a reserved section name becomes the document
title. Any text between the title and the first section is the description.

```markdown
# My Product
Short description of what this product does and who it's for.
```

### Releases section (required)

Defines the release swimlanes. Each `##` heading is a release.

For short release names (no spaces), no extra syntax is needed:
```markdown
# Releases
## MVP
## Beta
```

For longer names, add an `[id:: slug]` field. Stories then reference the slug
instead of the full name — this decouples display name from identifier:
```markdown
# Releases
## Minimum Viable Product [id:: mvp]
## Private Beta [id:: beta]
```

storymap will warn if a release name contains spaces and has no `[id::]`.

### Personas section (optional)

UX personas. Each `##` heading is a persona. Descriptions support full markdown.

```markdown
# Personas
## Alice the User
- **Role:** End user
- **Tech level:** Medium

Alice is a mid-level manager who accesses the app primarily on mobile.
```

### Map section (required)

The story map itself. Three levels of hierarchy:

```
## Activity    — column group (the backbone)
### Task        — column
#### Story      — card in a release swimlane
```

Each story is assigned to a release swimlane using `[release:: value]`. The
value must match the release name exactly (for releases without an id) or the
release id (for releases with `[id::]`). Stories without `[release::]` are
parsed but not shown in any swimlane.

```markdown
## User Management
### Authentication
#### Sign in [status:: done] [persona:: Alice the User] [release:: mvp]
User can log in with email and password.

#### SSO login [status:: in-progress] [release:: beta]
Support Google and Microsoft OAuth.

### Profile
#### Edit profile [status:: done] [release:: mvp]
#### Upload avatar [status:: not-started] [release:: beta]
```

### Story fields

Optional inline fields on the story heading using `[key:: value]` syntax.
Fields appear as badges on the rendered card.

| Field | Values |
|---|---|
| `status` | `not-started`, `in-progress`, `done`, `blocked` |
| `release` | Release name or id from `# Releases` section |
| `persona` | Any string matching a persona name |
| `deadline` | ISO date `YYYY-MM-DD` |

Any other `[key:: value]` field is accepted and rendered as a badge.

## Rules to follow

- Every task must have at least one story
- Every activity must have at least one task
- Every story should have a `[release::]` field — stories without one are invisible in the map
- Use `[id::]` on any release whose name contains spaces; omit it for short names like MVP
- Story names should be short (a few words) — put detail in the description
- Use the `status` field on every story so the map is readable at a glance

## Example

```markdown
# Task Manager App
A simple app for individuals to manage daily tasks.

# Releases
## MVP
Core task management — create, complete, delete.

## Private Beta [id:: beta]
Collaboration and sharing features.

# Personas
## Sam the Solo User
- **Tech level:** Medium
Uses the app daily to manage personal and work tasks.

# Map
## Task Management
### Create Tasks
#### Add a task [status:: done] [persona:: Sam the Solo User] [release:: MVP]
User can create a task with a title and optional due date.

#### Add subtasks [status:: not-started] [release:: beta]
Break tasks into smaller steps.

### Complete Tasks
#### Mark task as done [status:: done] [release:: MVP]
#### Bulk complete [status:: not-started] [release:: beta]
Select multiple tasks and mark them all done.

## Sharing
### Collaboration
#### Share task list [status:: not-started] [deadline:: 2026-09-01] [release:: MVP]
#### Assign tasks to others [status:: not-started] [release:: beta]
```
