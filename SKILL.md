---
name: storymap
description: >
  Create user story map markdown files in the MozaicWorks storymap format.
  Use this skill whenever the user asks to create, generate, or write a user
  story map, product backlog map, or story mapping document — even if they
  don't mention the file format explicitly. Also use when the user asks to
  add stories, activities, tasks, or releases to an existing storymap file,
  or when they ask to convert a list of features or requirements into a story
  map. Always use this skill before generating any .md file that represents
  a user story map.
---

# Storymap Skill

Generate valid `.md` files in the MozaicWorks storymap format. The user can
render them to HTML with `storymap render <file>`.

## File structure

```
# Optional Title
Optional description.

# Releases        ← required, defines swimlane labels
## Release 1
## Release 2

# Personas        ← optional
## Persona Name
Description with markdown.

# Map             ← required
## Activity       ← column group
### Task          ← column
#### Story [status:: done] [persona:: Name] [release:: Release 1] [deadline:: YYYY-MM-DD]
Optional story description.

#### Story in second swimlane [status:: not-started] [release:: Release 2]
```

## Rules

- `# Releases`, `# Personas`, `# Map` are reserved section names (case-insensitive)
- Any other `#` heading becomes the document title (first one) or is passed through
- Map hierarchy is strictly `##` Activity → `###` Task → `####` Story
- Each story is assigned to a release swimlane via `[release:: Release Name]`
- The `[release::]` value must exactly match a release name defined in `# Releases`
- Stories without a `[release::]` field are parsed but not shown in any swimlane
- Story names are short labels (a few words); put detail in the description body
- Always add `[status:: ...]` to every story — it drives the card color in the HTML
- Status values: `not-started`, `in-progress`, `done`, `blocked`
- Any `[key:: value]` field is valid and renders as a badge

## Output instructions

1. Output the storymap as a fenced markdown code block so the user can copy it
2. Name the suggested file after the product (e.g. `task-manager.md`)
3. After the code block, remind the user to run: `storymap render <filename>.md`
4. If the user hasn't specified releases, default to two: `MVP` and `Next`
5. If the user hasn't specified personas, omit the `# Personas` section
6. Aim for 3–6 activities, 2–4 tasks per activity, 1–3 stories per task per release

## Example

```markdown
# Task Manager
A simple app for individuals to manage daily tasks.

# Releases
## MVP
Core task management.

## Beta
Collaboration features.

# Personas
## Sam the Solo User
- **Tech level:** Medium

Uses the app daily for personal and work tasks.

# Map
## Task Management
### Create Tasks
#### Add a task [status:: done] [persona:: Sam the Solo User] [release:: MVP]
Title and optional due date.

#### Add subtasks [status:: not-started] [release:: Beta]

### Complete Tasks
#### Mark task as done [status:: done] [release:: MVP]
#### Bulk complete [status:: not-started] [release:: Beta]

## Sharing
### Collaboration
#### Share task list [status:: not-started] [release:: MVP]
#### Assign tasks [status:: not-started] [release:: Beta]
```
