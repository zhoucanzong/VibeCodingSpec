---
name: vibe-spec
description: Cross-agent spec-driven development workflow for maintaining projects with Claude, Codex, Cursor, and similar coding agents. Use when the user wants to initialize project specs, turn a feature idea into a maintainable specification, implement from a spec, inherit or update existing specs, review completed work against acceptance criteria, audit spec/code drift, or keep multiple agents aligned on project style and decisions.
argument-hint: <request> or init or spec <request> or build <spec-id> or review <spec-id> or update <spec-id> or audit or status
allowed-tools: [Read, Write, Edit, MultiEdit, Bash, Grep, Glob, WebSearch, WebFetch]
---

# Vibe Spec

> One line: keep coding agents aligned by making project intent, implementation work, inheritance, and review explicit.

User input: `$ARGUMENTS`

## Command Routing

If invoked as a slash command:

| Command | Purpose | Default output |
|---|---|---|
| `/vibe-spec init` | Create the project spec workspace | `.vibe-spec/` scaffold |
| `/vibe-spec spec <request>` | Convert a request into a spec | New or updated spec |
| `/vibe-spec build <spec-id>` | Implement an approved spec | Code changes and implementation notes |
| `/vibe-spec review <spec-id>` | Review implementation against the spec | Review verdict and required fixes |
| `/vibe-spec update <spec-id>` | Maintain or evolve an existing spec | Spec revision and changelog |
| `/vibe-spec audit` | Detect spec/code drift across the project | Audit report |
| `/vibe-spec status` | Summarize spec states and next actions | Status summary |

If invoked naturally, infer the closest route:

- "Set up specs for this repo" -> `init`
- "Write a spec for..." -> `spec`
- "Build this spec" -> `build`
- "Check whether this is done" -> `review`
- "Change the old spec so..." -> `update`
- "Find what is out of sync" -> `audit`

## Required Project Files

Use `.vibe-spec/` as the cross-agent source of truth:

```text
.vibe-spec/
  PROJECT_SPEC.md     # product goal, scope, users, boundaries
  AGENT_GUIDE.md      # handoff rules for Claude, Codex, Cursor, etc.
  STYLE_GUIDE.md      # engineering, UI, naming, and architecture preferences
  DECISIONS.md        # durable architectural/product decisions
  SPEC_INDEX.md       # all specs, states, parents, and next actions
  specs/              # feature specs
```

When running `init`, create these files if missing. If a file exists, preserve user content and only append missing sections when needed.

## Agent Intake Protocol

Before modifying code, read the project context in this order:

1. `.vibe-spec/AGENT_GUIDE.md`
2. `.vibe-spec/PROJECT_SPEC.md`
3. `.vibe-spec/SPEC_INDEX.md`
4. `.vibe-spec/STYLE_GUIDE.md`
5. `.vibe-spec/DECISIONS.md`
6. The relevant spec under `.vibe-spec/specs/`
7. Existing code, tests, and similar implementations

Do not rely on hidden memory from a previous agent. Treat `.vibe-spec/` and the repository as the current truth.

If `.vibe-spec/` is missing and the user asks for implementation work, either run `init` first or create the minimum project/spec files needed for the task.

## Spec States

Use these states consistently:

- `draft`: still being shaped
- `approved`: ready to implement
- `in_progress`: implementation started
- `implemented`: code changes are complete
- `reviewed`: implementation passed review
- `needs_changes`: review found required fixes
- `needs_sync`: parent or project-level spec changed
- `superseded`: replaced by another spec
- `deprecated`: intentionally retired

Update `SPEC_INDEX.md` whenever a spec state changes.

## Spec File Format

Create feature specs under `.vibe-spec/specs/` using this naming pattern:

```text
YYYY-MM-DD-short-kebab-title.md
```

Each spec must include:

```markdown
---
spec_id: short-kebab-title
status: draft
parent: none
extends: []
supersedes: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
owner_agent: unspecified
---

# Spec: Human Title

## Summary

## Context

## Goals

## Non-Goals

## Inherits From

## Adds

## Overrides

## Requirements

## Acceptance Criteria

## Implementation Notes

## Verification Plan

## Review Notes

## Changelog
```

Keep specs concrete enough for another agent to implement without guessing. Avoid turning specs into long essays.

## Inheritance Rules

When a spec extends another spec:

- List parents in `parent` or `extends`.
- Preserve inherited goals, constraints, style rules, and acceptance criteria unless explicitly overridden.
- Record new behavior under `Adds`.
- Record changed behavior under `Overrides`.
- Never silently invalidate a parent rule.
- If a parent changes, mark dependent specs as `needs_sync` until reviewed.
- If a spec replaces another, set `supersedes` on the new spec and mark the old spec `superseded`.

When updating a spec, append a short `Changelog` entry with date, agent, and reason.

## Default Workflows

### Init

Goal: make the repository handoff-ready for any coding agent.

1. Inspect the repository structure and tech stack.
2. Create `.vibe-spec/` files from the templates.
3. Fill obvious project details from the repo.
4. Leave unknowns as `TBD` instead of inventing product facts.
5. Add first entries to `SPEC_INDEX.md`.
6. Report what was initialized and what still needs user input.

### Spec

Goal: turn a request into an implementable, reviewable spec.

1. Read the required project files.
2. Search for related specs and code.
3. Decide whether to create, inherit, or update a spec.
4. Ask only if the request affects product direction, data model, permissions, billing, security, destructive behavior, or has mutually exclusive interpretations.
5. Write goals, non-goals, requirements, acceptance criteria, and verification plan.
6. Update `SPEC_INDEX.md`.

### Build

Goal: implement a spec while preserving project style.

1. Read the required project files and target spec.
2. Confirm the spec is `approved`, or proceed only if the user explicitly asks to build a draft.
3. Mark the spec `in_progress`.
4. Inspect existing patterns before editing.
5. Implement the smallest complete change that satisfies acceptance criteria.
6. Update `Implementation Notes` with changed files and rationale.
7. Run the verification plan or the closest available tests.
8. Mark the spec `implemented` only after implementation and verification evidence are recorded.

### Review

Goal: decide whether the implementation satisfies the spec.

1. Read the target spec, implementation notes, and changed code.
2. Check every acceptance criterion.
3. Check inherited constraints and overrides.
4. Look for behavior implemented outside the spec.
5. Run or inspect verification evidence.
6. Write a verdict in `Review Notes`: `Pass`, `Pass with Notes`, `Needs Work`, or `Blocked`.
7. Mark the spec `reviewed` only for passing work. Use `needs_changes` when required fixes remain.

### Update

Goal: evolve a spec without losing history.

1. Read the target spec and related parent/child specs.
2. Apply the requested change.
3. Record adds, overrides, compatibility notes, and changelog.
4. Mark affected children `needs_sync` when inherited behavior changes.
5. Update `SPEC_INDEX.md`.

### Audit

Goal: detect drift between specs and code.

Check for:

- Approved specs with no implementation.
- Implemented specs with no review.
- Reviewed specs whose acceptance criteria no longer match code behavior.
- Code features with no spec entry.
- Deprecated or superseded specs still referenced by active specs.
- Child specs that need sync after parent changes.
- Style or architecture decisions violated by recent changes.

Write findings as actionable items with severity and affected files/specs.

## Engineering Rules

- Read before editing.
- Prefer existing project patterns over new abstractions.
- Keep changes scoped to the active spec.
- Do not perform unrelated refactors.
- Do not introduce dependencies without a clear spec-level reason.
- Preserve user changes and existing git history.
- Update specs when implementation reveals a necessary product or technical decision.
- Treat tests, builds, lint checks, screenshots, or manual reproduction steps as verification evidence.
- If verification cannot run, record the reason and residual risk.

## Final Response Format

For completed work, answer briefly:

```markdown
Done.

Spec:
- `<spec-id>` -> `<state>`

Changed:
- ...

Verified:
- ...

Notes:
- ...
```

For review work, lead with the verdict and required fixes.

For audit work, lead with highest-severity drift findings.
