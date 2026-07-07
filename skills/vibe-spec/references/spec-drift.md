# Spec Drift Audit

Use this guide for `/vibe-spec audit`.

## Drift Types

### Missing Implementation

A spec is `approved` or `in_progress`, but no implementation notes or matching code changes exist.

### Missing Review

A spec is `implemented`, but review notes are empty or no verdict exists.

### Untracked Behavior

Code contains meaningful product behavior with no related spec entry.

### Stale Acceptance

Acceptance criteria describe behavior that no longer matches code.

### Inheritance Drift

A parent spec changed but child specs were not reviewed or marked `needs_sync`.

### Decision Drift

Code or specs contradict `DECISIONS.md`.

### Style Drift

Implementation repeatedly violates `STYLE_GUIDE.md` or established code patterns.

## Audit Method

1. Read `.vibe-spec/SPEC_INDEX.md`.
2. Scan `.vibe-spec/specs/` for states, parents, supersession, and review notes.
3. Inspect recent git history when available.
4. Search code for features named in specs.
5. Search specs for code paths mentioned in implementation notes.
6. Compare decisions and style rules against recent changes.
7. Report actionable findings.

## Severity

- `P0`: shipped behavior violates a critical spec, security, privacy, data, or payment rule.
- `P1`: active feature behavior conflicts with acceptance criteria.
- `P2`: spec state, review evidence, or implementation notes are stale.
- `P3`: documentation hygiene issue with low immediate risk.

## Audit Output

```markdown
# Vibe Spec Audit

## Verdict

Healthy | Drift Found | Blocked

## Findings

| Severity | Type | Spec/File | Evidence | Action |
|---|---|---|---|---|

## State Summary

| State | Count |
|---|---:|

## Recommended Next Actions

- ...
```
