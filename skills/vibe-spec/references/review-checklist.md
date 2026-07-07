# Review Checklist

Use this checklist for `/vibe-spec review <spec-id>`.

## Verdicts

- `Pass`: implementation satisfies the spec and verification is adequate.
- `Pass with Notes`: acceptable, with non-blocking follow-ups.
- `Needs Work`: required fixes remain.
- `Blocked`: cannot reach a verdict due to missing access, missing data, or unclear requirements.

## Acceptance

- Every acceptance criterion is checked.
- Each checked criterion has evidence.
- Unchecked criteria are explained.
- Criteria added during implementation are reflected in the spec.

## Inheritance

- Parent specs still apply.
- Overrides are explicit.
- No inherited behavior was silently removed.
- Child specs are marked `needs_sync` if parent behavior changed.

## Code Quality

- Implementation follows existing project patterns.
- No unrelated refactors are mixed in.
- New abstractions have a clear reason.
- Error, loading, empty, and edge states are handled where relevant.
- Inputs and permissions are handled at appropriate boundaries.

## Verification

- Existing tests were run when available.
- Build or lint checks were run when relevant.
- Manual verification steps are specific enough to reproduce.
- Screenshots or browser checks are included for visual UI work when feasible.
- Skipped checks include a reason and residual risk.

## Documentation Sync

- Implementation notes list changed files and rationale.
- New decisions are recorded in `DECISIONS.md`.
- `SPEC_INDEX.md` has current status and next action.
- Superseded or deprecated specs are marked consistently.

## Review Output

Write review notes in this shape:

```markdown
## Review Notes

### Verdict

Pass | Pass with Notes | Needs Work | Blocked

### Acceptance Checklist

- [x] Criterion - evidence
- [ ] Criterion - required fix

### Findings

| Severity | Issue | Evidence | Required Fix |
|---|---|---|---|

### Verification Evidence

- Command or manual check: result

### Follow-ups

- Non-blocking item
```
