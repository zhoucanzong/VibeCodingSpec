# Style Guide

## Engineering Style

- Prefer existing project patterns and local helpers.
- Keep changes small and directly tied to the active spec.
- Avoid unrelated refactors.
- Add abstractions only when they reduce real duplication or match an established pattern.
- Do not introduce dependencies without a clear reason.

## Frontend Style

- Build the usable product surface, not a marketing placeholder.
- Match existing design systems and component conventions.
- Include important states: loading, empty, error, success, disabled.
- Keep interfaces clear, scannable, and responsive.
- Avoid decorative UI that does not help the workflow.

## Backend Style

- Validate inputs at boundaries.
- Preserve authorization and privacy assumptions.
- Handle errors explicitly.
- Prefer idempotent operations for retryable workflows.
- Record important API or data model decisions in `DECISIONS.md`.

## Naming

- Use existing naming conventions in the repository.
- Prefer clear domain names over generic helper names.
