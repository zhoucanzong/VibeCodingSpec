# Agent Compatibility

Use these rules when the same project may be maintained by Claude, Codex, Cursor, or other coding agents.

## Portable Instructions

- Put durable project facts in `.vibe-spec/`, not in tool-specific memory.
- Prefer plain Markdown files over hidden configuration formats.
- Keep commands understandable as both slash commands and natural language.
- Treat frontmatter as helpful metadata, but never make critical behavior depend only on one tool's parser.
- Record assumptions in specs when an agent proceeds without asking the user.

## Claude-Friendly Conventions

- Keep `argument-hint` short and command-like.
- Use `allowed-tools` as an affordance for Claude-style skill runners.
- Write command routes explicitly, such as `/vibe-spec build <spec-id>`.

## Codex-Friendly Conventions

- Put trigger conditions in the `description` field.
- Put all required behavior in the Markdown body.
- Do not require slash command syntax; support natural-language equivalents.
- Prefer repository files and explicit verification evidence over conversation memory.

## Cursor And IDE Agents

- Keep `.vibe-spec/AGENT_GUIDE.md` as the first file for handoff.
- Link specs to changed code paths in implementation notes.
- Keep `SPEC_INDEX.md` current so agents can discover the active work without scanning every file.

## Handoff Discipline

Every agent should leave the next agent with:

- Current spec state.
- Changed files.
- Verification commands and results.
- Known risks or skipped checks.
- Follow-up tasks if work is not fully reviewed.
