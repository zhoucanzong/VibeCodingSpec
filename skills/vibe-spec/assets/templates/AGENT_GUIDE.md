# Agent Guide

## Intake Order

Before changing code, read:

1. `.vibe-spec/PROJECT_SPEC.md`
2. `.vibe-spec/SPEC_INDEX.md`
3. `.vibe-spec/STYLE_GUIDE.md`
4. `.vibe-spec/DECISIONS.md`
5. `.vibe-spec/FILE_MAP.md`
6. `.vibe-spec/DATA_GUIDE.md` when data, fixtures, persistence, or generated artifacts are involved
7. `.vibe-spec/TESTING_GUIDE.md` before running, adding, or changing tests
8. `.vibe-spec/EXPERIMENTS.md` when doing benchmark, model, prompt, data, or performance work
9. Relevant files under `.vibe-spec/specs/`
10. Existing code and tests related to the task

## Cross-Agent Rules

- Treat this repository and `.vibe-spec/` as the current source of truth.
- Do not rely on memory from another tool or previous session.
- Preserve existing user changes.
- Keep implementation scoped to the active spec.
- Update spec state and implementation notes when work progresses.
- Record verification evidence before marking work implemented or reviewed.
- Keep `FILE_MAP.md` current when important files or directories are added, removed, or repurposed.
- Record data locations, fixtures, and generated artifacts in `DATA_GUIDE.md`.
- Record test commands and project-local verification scripts in `TESTING_GUIDE.md`.
- Record experiments with enough detail for another agent to reproduce them.

## When To Ask The User

Ask before proceeding when work affects:

- Product direction or user-facing behavior with multiple valid interpretations.
- Database schema, migrations, or persisted data.
- Authentication, authorization, payment, security, or privacy boundaries.
- Destructive operations or large rewrites.
- External service contracts.

Otherwise, make a reasonable project-consistent assumption and record it.
