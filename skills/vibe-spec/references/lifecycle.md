# Lifecycle Guide

Use this guide when creating, implementing, updating, or retiring specs.

## Spec Creation

Create a new spec when:

- The user asks for a new feature, workflow, integration, or meaningful bug fix.
- The work has acceptance criteria worth tracking.
- The implementation will affect multiple files or future behavior.
- Multiple agents may touch the work over time.

Update an existing spec when:

- The request is a refinement of a tracked behavior.
- The work changes an accepted requirement.
- The work fixes a gap found during review.

Avoid creating a spec for:

- Tiny copy edits.
- Mechanical formatting.
- One-line internal fixes with no product behavior change.

## Approval

A spec is `approved` when:

- Goals and non-goals are clear.
- Acceptance criteria are checkable.
- Inheritance and overrides are explicit.
- Verification plan is realistic for the repository.

If the user explicitly asks to implement before approval, proceed but mark the spec state and risk clearly.

## Implementation

During implementation:

- Mark the spec `in_progress`.
- Keep changes scoped to the spec.
- Update implementation notes as facts emerge.
- If implementation requires behavior not covered by the spec, update the spec first.

Mark `implemented` only when:

- Code changes are complete.
- Acceptance criteria have matching implementation notes.
- Verification evidence is recorded.

## Review

Mark `reviewed` only when:

- All required acceptance criteria pass.
- Inherited constraints are still honored.
- Verification evidence is adequate.
- No required fixes remain.

Use `needs_changes` when implementation is close but not acceptable.
Use `blocked` in review notes when external input or missing access prevents a verdict.

## Supersession And Deprecation

Use `superseded` when a newer spec replaces an older one.
Use `deprecated` when behavior is intentionally retired without replacement.

Always update:

- The old spec status.
- The new spec `supersedes` field.
- `SPEC_INDEX.md`.
- Any child specs that inherit from the old behavior.
