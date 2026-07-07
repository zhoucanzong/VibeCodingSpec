# Testing Guide

Use this file to make verification reproducible across agents.

## Standard Commands

| Purpose | Command | When To Run | Notes |
|---|---|---|---|
| Install dependencies | TBD | Fresh checkout | TBD |
| Unit tests | TBD | Logic changes | TBD |
| Integration tests | TBD | API/data changes | TBD |
| Lint | TBD | Before review | TBD |
| Build | TBD | Before marking implemented | TBD |

## Test Scripts

Project-local test or verification scripts should live in one of:

- Existing project test/script directories.
- `.vibe-spec/scripts/` for spec workflow helpers that do not belong to product code.

Every script should document:

- Purpose.
- Inputs.
- Outputs.
- Required environment variables.
- Example command.

## Fixtures

| Path | Purpose | Related Spec | Notes |
|---|---|---|---|
| TBD | TBD | TBD | TBD |

## Manual Verification

Use manual verification only when automated coverage is unavailable or insufficient. Record exact steps, expected result, actual result, and environment.

## Visual Verification

For UI work, record viewport, browser, route, screenshots if available, and any known visual risk.
