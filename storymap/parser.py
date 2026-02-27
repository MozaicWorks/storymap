"""
Parser for storymap markdown documents.

Uses markdown-it-py to tokenize the input, then walks the token stream
as a state machine to build a StorymapDocument.

Section headings (h1) drive state transitions:
    # Releases  → RELEASES state
    # Personas  → PERSONAS state
    # Map       → MAP state

Within each state, h2/h3/h4 headings drive entity creation.
Stories are assigned to releases via the [release:: name] field — no
positional separators needed.
Descriptions are extracted from raw source lines using token.map offsets,
preserving the original markdown for downstream rendering.

[key:: value] inline fields on story headings are extracted via regex,
not a custom markdown-it-py plugin, keeping the parser self-contained.
"""

import re
from enum import Enum, auto

from markdown_it import MarkdownIt

from storymap.model import Activity, Persona, Release, Story, StorymapDocument, Task


# Matches [key:: value] or [key::value] — key is a word with optional hyphens.
FIELD_PATTERN = re.compile(r"\[(\w[\w-]*)::[ \t]*([^\]]*)\]")

# Reserved h1 section names (case-insensitive).
_SECTION_RELEASES = "releases"
_SECTION_PERSONAS = "personas"
_SECTION_MAP = "map"


class _Section(Enum):
    START = auto()
    TITLE = auto()
    RELEASES = auto()
    PERSONAS = auto()
    MAP = auto()


class StorymapParser:
    """Parse a storymap markdown document into a StorymapDocument."""

    def parse(self, text: str) -> StorymapDocument:
        # Disable setext headings (text followed by --- or ===) so that
        # --- is always parsed as a thematic break (hr), never as h2.
        # Our format uses ATX headings exclusively (# ## ### ####).
        md = MarkdownIt()
        md.disable("lheading")
        tokens = md.parse(text)
        lines = text.splitlines()

        doc = StorymapDocument()
        section = _Section.START

        current_release: Release | None = None
        current_persona: Persona | None = None
        current_activity: Activity | None = None
        current_task: Task | None = None
        current_story: Story | None = None
        desc_start: int = 0

        # ------------------------------------------------------------------
        # Helpers — closures over the local state variables above.
        # ------------------------------------------------------------------

        def extract_desc(end_line: int) -> str:
            return _extract_lines(lines, desc_start, end_line)

        def finalize_story(end_line: int) -> None:
            nonlocal current_story
            if current_story is not None:
                current_story.description = extract_desc(end_line)
                current_story = None

        def finalize_task(end_line: int) -> None:
            nonlocal current_task
            if current_task is not None:
                finalize_story(end_line)
                if current_activity is not None:
                    current_activity.tasks.append(current_task)
                current_task = None

        def finalize_activity(end_line: int) -> None:
            nonlocal current_activity
            if current_activity is not None:
                finalize_task(end_line)
                doc.activities.append(current_activity)
                current_activity = None

        def finalize_release(end_line: int) -> None:
            nonlocal current_release
            if current_release is not None:
                current_release.description = extract_desc(end_line)
                doc.releases.append(current_release)
                current_release = None

        def finalize_persona(end_line: int) -> None:
            nonlocal current_persona
            if current_persona is not None:
                current_persona.description = extract_desc(end_line)
                doc.personas.append(current_persona)
                current_persona = None

        def finalize_title(end_line: int) -> None:
            if section == _Section.TITLE:
                doc.description = extract_desc(end_line)

        def finalize_section(end_line: int) -> None:
            """Flush the current section before transitioning to a new one."""
            if section == _Section.TITLE:
                finalize_title(end_line)
            elif section == _Section.RELEASES:
                finalize_release(end_line)
            elif section == _Section.PERSONAS:
                finalize_persona(end_line)
            elif section == _Section.MAP:
                finalize_activity(end_line)

        # ------------------------------------------------------------------
        # Token walk
        # ------------------------------------------------------------------

        for i, token in enumerate(tokens):

            if token.type == "heading_open":
                level = int(token.tag[1])  # "h1" → 1, "h4" → 4
                content = _heading_content(tokens, i)
                token_start = _map_start(token)
                token_end = _map_end(token)

                if level == 1:
                    finalize_section(token_start)
                    keyword = content.strip().lower()
                    if keyword == _SECTION_RELEASES:
                        section = _Section.RELEASES
                    elif keyword == _SECTION_PERSONAS:
                        section = _Section.PERSONAS
                    elif keyword == _SECTION_MAP:
                        section = _Section.MAP
                    elif section == _Section.START and doc.title is None:
                        doc.title = content.strip()
                        section = _Section.TITLE
                        desc_start = token_end
                    else:
                        doc.warnings.append(
                            f"Line {token_start + 1}: unrecognised section "
                            f"'# {content.strip()}' — ignored."
                        )

                elif level == 2:
                    if section == _Section.RELEASES:
                        finalize_release(token_start)
                        rel_name, rel_fields = _parse_story_heading(content.strip())
                        current_release = Release(
                            name=rel_name,
                            id=rel_fields.get("id") or None,
                        )
                        desc_start = token_end

                    elif section == _Section.PERSONAS:
                        finalize_persona(token_start)
                        current_persona = Persona(name=content.strip())
                        desc_start = token_end

                    elif section == _Section.MAP:
                        finalize_activity(token_start)
                        current_activity = Activity(name=content.strip())
                        desc_start = token_end

                elif level == 3:
                    if section == _Section.MAP:
                        finalize_task(token_start)
                        if current_activity is None:
                            doc.warnings.append(
                                f"Line {token_start + 1}: task "
                                f"'### {content.strip()}' has no parent activity — ignored. "
                                "Tasks must appear under a '## Activity' heading."
                            )
                        else:
                            current_task = Task(name=content.strip())
                            desc_start = token_end

                elif level == 4:
                    if section == _Section.MAP:
                        if current_task is None:
                            doc.warnings.append(
                                f"Line {token_start + 1}: story "
                                f"'#### {content.strip()}' has no parent task — ignored. "
                                "Stories must appear under a '### Task' heading."
                            )
                        else:
                            finalize_story(token_start)
                            name, fields = _parse_story_heading(content)
                            current_story = Story(name=name, fields=fields)
                            current_task.stories.append(current_story)
                            desc_start = token_end

        # ------------------------------------------------------------------
        # Flush any remaining open entities after the last token.
        # ------------------------------------------------------------------
        finalize_section(len(lines))

        _warn_unmatched_releases(doc)

        return doc


# ---------------------------------------------------------------------------
# Module-level helpers (pure functions, no state)
# ---------------------------------------------------------------------------


def _warn_unmatched_releases(doc: StorymapDocument) -> None:
    """Warn about stories whose [release::] value doesn't match any release key."""
    release_keys = {r.key() for r in doc.releases}
    for activity in doc.activities:
        for task in activity.tasks:
            for story in task.stories:
                r = story.release()
                if r is not None and r not in release_keys:
                    doc.warnings.append(
                        f"Story '{story.name}': release '{r}' not found in "
                        "Releases section — story will not appear in any swimlane."
                    )


def _heading_content(tokens: list, heading_open_index: int) -> str:
    """Return the inline content of the heading that follows heading_open."""
    next_index = heading_open_index + 1
    if next_index < len(tokens) and tokens[next_index].type == "inline":
        return tokens[next_index].content
    return ""


def _map_start(token) -> int:
    return token.map[0] if token.map else 0


def _map_end(token) -> int:
    return token.map[1] if token.map else 0


def _extract_lines(lines: list[str], start: int, end: int) -> str:
    """
    Extract raw markdown lines from [start, end), stripping leading and
    trailing blank lines.  Returns an empty string if the range is empty.
    """
    if start >= end:
        return ""
    extracted = list(lines[start:end])
    while extracted and not extracted[0].strip():
        extracted.pop(0)
    while extracted and not extracted[-1].strip():
        extracted.pop()
    return "\n".join(extracted)


def _parse_story_heading(text: str) -> tuple[str, dict[str, str]]:
    """
    Split a story heading into its display name and [key:: value] fields.

    Example:
        "Login [status:: done] [release:: MVP]"
        → ("Login", {"status": "done", "release": "MVP"})
    """
    fields: dict[str, str] = {}
    for match in FIELD_PATTERN.finditer(text):
        fields[match.group(1)] = match.group(2).strip()
    name = FIELD_PATTERN.sub("", text).strip()
    return name, fields
