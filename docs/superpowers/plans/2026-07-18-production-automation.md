# vibe-spec Production Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `vibe-spec` 完善为 Agent-first、跨工具可接续、具有生产级生命周期自动化与可选 CI/hooks 的 Skill。

**Architecture:** `SKILL.md` 负责场景判断、用户交互和审查编排；标准库 Python 脚本只处理确定性文件操作。共享核心统一解析 spec、状态机、索引和 JSON 结果，Markdown 始终是长期事实来源。

**Tech Stack:** Markdown、Python 3.10+ 标准库、`unittest`、GitHub Actions、POSIX Git hooks。

## Global Constraints

- 保持 Agent-first，不构建独立 CLI 产品、服务、数据库或厂商 SDK。
- Python 3.10+，不添加第三方运行时依赖。
- 所有已有用户文件默认保留，无法安全合并时返回错误。
- `CLAUDE.md`、`AGENTS.md` 仅作为薄入口，不复制项目规则。
- Markdown 是唯一持久事实来源；JSON 只作为即时命令输出。
- 脚本不能冒充独立工程审查；subagent 由当前 coding agent 调度。

---

### Task 1: Shared Core and Context Templates

**Files:**
- Create: `skills/vibe-spec/scripts/vibe_spec_core.py`
- Create: `skills/vibe-spec/assets/templates/HANDOFF.md`
- Create: `skills/vibe-spec/assets/templates/ROADMAP.md`
- Create: `skills/vibe-spec/tests/test_core.py`

**Interfaces:**
- Produces: `SpecDocument`, `CommandResult`, `find_spec()`, `load_spec()`, `write_spec()`, `replace_section()`, `append_lifecycle()`, `rebuild_spec_index()` and `emit_result()`.
- Produces: stable result keys `ok`, `command`, `changes`, `findings`, `next_actions`.

- [x] **Step 1: Write failing core tests**

Test frontmatter scalar/list parsing, section replacement, lifecycle append, duplicate spec detection, index rebuild and JSON result shape with real temporary files.

- [x] **Step 2: Verify RED**

Run: `python3 -m unittest skills/vibe-spec/tests/test_core.py -v`

Expected: import failure because `vibe_spec_core.py` does not exist.

- [x] **Step 3: Implement the minimal shared core**

Use standard-library dataclasses and atomic `Path.replace()` writes. Parse only the constrained frontmatter grammar used by the templates.

- [x] **Step 4: Add context templates**

`HANDOFF.md` contains current goal, active specs, working state, recent verification, blockers, worktree risks and next action. `ROADMAP.md` contains `Now`, `Next`, `Later`, and `Done` tables with spec links.

- [x] **Step 5: Verify GREEN**

Run: `python3 -m unittest skills/vibe-spec/tests/test_core.py -v`

Expected: all Task 1 tests pass.

### Task 2: Initialization and Context Continuity

**Files:**
- Modify: `skills/vibe-spec/scripts/init_vibe_spec.py`
- Create: `skills/vibe-spec/scripts/refresh_context.py`
- Create: `skills/vibe-spec/assets/templates/AGENT_ENTRY.md`
- Create: `skills/vibe-spec/assets/templates/github-actions-vibe-spec.yml`
- Modify: `skills/vibe-spec/assets/templates/AGENT_GUIDE.md`
- Modify: `skills/vibe-spec/assets/templates/FILE_MAP.md`
- Create: `skills/vibe-spec/tests/test_init_and_context.py`

**Interfaces:**
- `init_vibe_spec.py TARGET --profile PROFILE [--modules ...] [--agent-entry claude codex] [--ci] [--json]`.
- `refresh_context.py TARGET [--json]` prints repository-map candidates and never changes `FILE_MAP.md`.

- [x] **Step 1: Write failing initialization tests**

Cover HANDOFF/ROADMAP creation, optional thin entries, optional CI, idempotency, JSON output and preservation of existing entry files.

- [x] **Step 2: Verify RED**

Run: `python3 -m unittest skills/vibe-spec/tests/test_init_and_context.py -v`

Expected: failures for unsupported arguments and missing context files.

- [x] **Step 3: Implement init options and candidate scanning**

Map `claude` to `CLAUDE.md` and `codex` to `AGENTS.md`. Render a short pointer to `.vibe-spec/HANDOFF.md` and `.vibe-spec/AGENT_GUIDE.md`. Scan tracked/top-level project paths while excluding VCS, caches, build output and `.vibe-spec`.

- [x] **Step 4: Verify GREEN**

Run: `python3 -m unittest skills/vibe-spec/tests/test_init_and_context.py -v`

Expected: all Task 2 tests pass.

### Task 3: Spec Creation and Lifecycle State Machine

**Files:**
- Create: `skills/vibe-spec/scripts/create_spec.py`
- Create: `skills/vibe-spec/scripts/promote_spec.py`
- Create: `skills/vibe-spec/tests/test_lifecycle.py`
- Modify: `skills/vibe-spec/assets/templates/FEATURE_SPEC.md`

**Interfaces:**
- `create_spec.py TARGET SPEC_ID --title TITLE [--parent ID] [--owner-agent NAME] [--json]`.
- `promote_spec.py TARGET SPEC_ID STATE --reason TEXT [--evidence TEXT] [--json]`.
- State transitions and gate findings are exposed by `vibe_spec_core.py`.

- [x] **Step 1: Write failing lifecycle tests**

Cover valid creation, normalized IDs, duplicate rejection, allowed transitions, illegal jumps, content gates, no-write-on-failure and synchronized frontmatter/log/index updates.

- [x] **Step 2: Verify RED**

Run: `python3 -m unittest skills/vibe-spec/tests/test_lifecycle.py -v`

Expected: import or command failures because lifecycle scripts do not exist.

- [x] **Step 3: Implement creation and promotion**

Validate before writes. Require meaningful specification content before `ready_for_review`/`approved`, implementation notes before `implemented`, verification evidence before `verified`, and review notes before `reviewed`/`active`.

- [x] **Step 4: Verify GREEN**

Run: `python3 -m unittest skills/vibe-spec/tests/test_lifecycle.py -v`

Expected: all Task 3 tests pass.

### Task 4: Review, Retirement, Status and Context Updates

**Files:**
- Create: `skills/vibe-spec/scripts/create_review.py`
- Create: `skills/vibe-spec/scripts/prepare_review_context.py`
- Create: `skills/vibe-spec/scripts/status_vibe_spec.py`
- Create: `skills/vibe-spec/scripts/update_handoff.py`
- Create: `skills/vibe-spec/tests/test_review_status.py`
- Modify: `skills/vibe-spec/assets/templates/REVIEW_REPORT.md`

**Interfaces:**
- `create_review.py TARGET SPEC_ID --verdict pass|changes --mode subagent|self --summary TEXT [--finding TEXT] [--json]`.
- `prepare_review_context.py TARGET SPEC_ID [--base REF] [--output PATH] [--json]`.
- `status_vibe_spec.py TARGET [--json]`.
- `update_handoff.py TARGET --goal TEXT --state TEXT --next-action TEXT [--active-spec ID] [--blocker TEXT] [--verification TEXT] [--json]`.

- [ ] **Step 1: Write failing workflow tests**

Cover report creation, spec review-note linkage, sanitized review context, current-state summary, roadmap summary, handoff update and stable JSON fields.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest skills/vibe-spec/tests/test_review_status.py -v`

Expected: failures because workflow scripts do not exist.

- [ ] **Step 3: Implement workflow commands**

Do not include implementer conclusions in review context. Record review mode and report path in the spec. Keep handoff sections concise and replace only owned sections.

- [ ] **Step 4: Verify GREEN**

Run: `python3 -m unittest skills/vibe-spec/tests/test_review_status.py -v`

Expected: all Task 4 tests pass.

### Task 5: Strict Health Checks, CI and Hooks

**Files:**
- Modify: `skills/vibe-spec/scripts/check_vibe_spec.py`
- Create: `skills/vibe-spec/scripts/install_git_hooks.py`
- Create: `skills/vibe-spec/tests/test_check_and_hooks.py`

**Interfaces:**
- `check_vibe_spec.py TARGET [--strict] [--json]` checks index parity, duplicate IDs, parent/extends references, lifecycle evidence, handoff and roadmap.
- `install_git_hooks.py TARGET [--force] [--json]` creates managed `pre-commit` and `pre-push` hooks and refuses to replace unmanaged hooks unless `--force`.

- [ ] **Step 1: Write failing governance tests**

Cover orphan index rows, unindexed specs, broken references, stale/missing handoff data, JSON findings and non-overwrite hook behavior.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest skills/vibe-spec/tests/test_check_and_hooks.py -v`

Expected: failures for missing checks and hook installer.

- [ ] **Step 3: Implement checks and explicit hook installation**

Hooks locate the repository root and invoke copied `.vibe-spec/scripts/check_vibe_spec.py` when available. Existing unmanaged hooks cause a clear error without mutation.

- [ ] **Step 4: Verify GREEN**

Run: `python3 -m unittest skills/vibe-spec/tests/test_check_and_hooks.py -v`

Expected: all Task 5 tests pass.

### Task 6: Skill Guidance, Metadata and Deployment Validation

**Files:**
- Modify: `skills/vibe-spec/SKILL.md`
- Create: `skills/vibe-spec/references/automation.md`
- Modify: `skills/vibe-spec/references/agent-compatibility.md`
- Modify: `README.md`
- Create: `skills/vibe-spec/agents/openai.yaml`
- Create: `skills/vibe-spec/tests/test_skill_contract.py`

**Interfaces:**
- Skill routes `init`, `context`, `handoff`, `roadmap`, `spec`, `promote`, `review`, `status`, `check`, `sync`, and `retire` while preserving natural-language use.
- `agents/openai.yaml` exposes Chinese display metadata and a default prompt that invokes `$vibe-spec`.

- [ ] **Step 1: Write failing contract tests**

Assert concise valid frontmatter, required command/resource routing, Agent-first language, context start/end protocol, subagent review path and fallback path.

- [ ] **Step 2: Verify RED**

Run: `python3 -m unittest skills/vibe-spec/tests/test_skill_contract.py -v`

Expected: failures for missing metadata and new routes.

- [ ] **Step 3: Update Skill and documentation**

Keep `SKILL.md` below 500 lines by moving command details to `references/automation.md`. Preserve Chinese instructions and English machine keys/status values.

- [ ] **Step 4: Verify GREEN and full suite**

Run: `python3 -m unittest discover -s skills/vibe-spec/tests -v`

Expected: all tests pass with zero failures.

- [ ] **Step 5: Validate the skill package**

Run the available `quick_validate.py` against `skills/vibe-spec`, compile all scripts, run `git diff --check`, initialize a production fixture and execute strict check/status JSON smoke tests.

Expected: every command exits 0 and generated cross-Agent context is readable from the fixed handoff entry.

- [ ] **Step 6: Review, commit and push**

Review the full diff against the design, fix all critical/important findings, commit implementation, then push `main` to `origin`.
