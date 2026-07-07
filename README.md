# Vibe Spec

Cross-agent spec-driven development workflow for Claude, Codex, Cursor, and similar coding agents.

`vibe-spec` helps a project keep product intent, implementation work, spec inheritance, and review evidence synchronized across different coding tools.

## What It Does

- Initializes a project-level `.vibe-spec/` workspace.
- Turns feature ideas into maintainable specs.
- Supports spec inheritance, overrides, supersession, and sync states.
- Guides agents to implement from specs instead of hidden assumptions.
- Reviews completed work against acceptance criteria.
- Audits spec/code drift across a repository.
- Maintains a file map so agents know what important files and directories do.
- Standardizes experiment logs, data locations, fixtures, and verification scripts.

## Install

Ask your coding agent to install this skill from the repository:

```text
Install this skill: git@github.com:zhoucanzong/VibeCodingSpec.git
```

The skill lives at:

```text
skills/vibe-spec/SKILL.md
```

## Usage

Claude-style slash command examples:

```text
/vibe-spec init
/vibe-spec spec Add passwordless login
/vibe-spec build passwordless-login
/vibe-spec review passwordless-login
/vibe-spec update passwordless-login
/vibe-spec experiment login-benchmark
/vibe-spec audit
/vibe-spec status
```

Natural language examples for Codex or other agents:

```text
Use vibe-spec to initialize this repo.
Use vibe-spec to write a spec for passwordless login.
Use vibe-spec to implement the approved passwordless-login spec.
Use vibe-spec to audit this project for spec drift.
```

## Project Workspace

When initialized in a target project, `vibe-spec` uses:

```text
.vibe-spec/
  PROJECT_SPEC.md
  AGENT_GUIDE.md
  STYLE_GUIDE.md
  DECISIONS.md
  FILE_MAP.md
  DATA_GUIDE.md
  TESTING_GUIDE.md
  EXPERIMENTS.md
  SPEC_INDEX.md
  specs/
  reports/
  scripts/
```

These files are the handoff layer between agents. Claude, Codex, Cursor, and future tools should read them before changing code.

## Skill Structure

```text
skills/
  vibe-spec/
    SKILL.md
    assets/
      templates/
        AGENT_GUIDE.md
        DECISIONS.md
        DATA_GUIDE.md
        EXPERIMENTS.md
        FEATURE_SPEC.md
        FILE_MAP.md
        PROJECT_SPEC.md
        REVIEW_REPORT.md
        AUDIT_REPORT.md
        SPEC_INDEX.md
        STYLE_GUIDE.md
        TESTING_GUIDE.md
    references/
      agent-compatibility.md
      lifecycle.md
      review-checklist.md
      spec-drift.md
    scripts/
      init_vibe_spec.py
```

## Core Idea

Specs should not be one-off planning artifacts. They should evolve with the project:

- A spec can inherit from project-level rules or parent specs.
- A spec can add behavior or explicitly override inherited behavior.
- Implementation notes record what changed and why.
- Reviews record whether acceptance criteria were actually satisfied.
- Audits catch drift when code and specs diverge.
- Experiments record inputs, commands, metrics, artifacts, and decision impact.
- Data and testing guides make verification reproducible across tools.
