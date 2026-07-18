# 自动化与手工降级

只在执行对应命令时读取本文件。脚本均使用 Python 3.10+ 标准库，可直接运行，也可复制到目标项目 `.vibe-spec/scripts/`。

## 通用输出

主要命令支持 `--json`，固定字段为：

```json
{"ok": true, "command": "status", "changes": [], "findings": [], "next_actions": []}
```

JSON 是即时输出，不持久化第二套项目状态。

## Init

```bash
scripts/init_vibe_spec.py <repo> --profile minimal
scripts/init_vibe_spec.py <repo> --profile standard --modules data experiments
scripts/init_vibe_spec.py <repo> --profile production --agent-entry claude codex --ci
```

- `--agent-entry claude codex cursor`：可选生成薄入口，已有文件保留。
- `--ci`：可选生成 `.github/workflows/vibe-spec.yml`。
- production 或 scripts 模块会把治理脚本复制到 `.vibe-spec/scripts/`。

手工降级：从 `assets/templates/` 复制 profile 需要的缺失文件，创建 `specs/`，按需创建 `reports/` 和 `scripts/`，再更新 `MODULES.md`。不得覆盖已有文件。

## Context 与 Handoff

```bash
scripts/refresh_context.py <repo> --json
scripts/update_handoff.py <repo> \
  --goal "当前目标" \
  --state in_progress \
  --active-spec spec-id \
  --verification "tests: PASS" \
  --next-action "执行 review" \
  --json
scripts/status_vibe_spec.py <repo> --json
```

`refresh_context.py` 只输出代码地图候选，不修改 `FILE_MAP.md`。Agent 核对目录职责和依赖方向后再合并。

手工降级：只替换 `HANDOFF.md` 的 Current Goal、Active Specs、Working State、Recent Verification、Blockers、Worktree Risks 和 Next Action；保留 Context Links 及用户扩展章节。

`roadmap` 没有机械脚本。Agent 直接维护 `ROADMAP.md` 的 Now、Next、Later、Done，进入 Now 前关联 spec。

## Spec 与生命周期

```bash
scripts/create_spec.py <repo> login-flow --title "Login Flow" --parent project --owner-agent codex --json
scripts/promote_spec.py <repo> login-flow ready_for_review \
  --reason "规格已完整" --evidence "acceptance criteria reviewed" --actor codex --json
```

`promote_spec.py` 先检查合法路径和内容门禁，失败时不写文件；成功时同步 frontmatter、Lifecycle Log、Changelog 和 `SPEC_INDEX.md`。

- `sync`：从 `active` 推进到 `needs_sync`，核对父规则，更新 spec 后进入 `draft` 并重新审核。
- `retire`：从 `active` 推进到 `superseded` 或 `deprecated`，完成引用迁移后推进到 `archived`。
- `update`：从 `active` 推进到 `needs_update`，修改后回到 `draft`。

手工降级：严格使用 `references/lifecycle-governance.md` 的状态图；写入相同的 frontmatter、Lifecycle Log、Changelog 和索引更新。

## Review

```bash
scripts/prepare_review_context.py <repo> login-flow --base origin/main --json
scripts/create_review.py <repo> login-flow \
  --verdict pass --mode subagent --summary "验收标准全部满足" --json
```

审查包故意排除 Implementation Notes 和 Review Notes 中的实现者结论。Agent 负责启动 subagent；脚本不能启动或伪装 reviewer。

不支持 subagent 时，按 `references/review-checklist.md` 自审，并使用 `--mode self` 记录限制。

## Check、CI 与 Hooks

```bash
scripts/check_vibe_spec.py <repo>
scripts/check_vibe_spec.py <repo> --strict --json
scripts/install_git_hooks.py <repo> --json
```

- 默认 P0/P1 返回非零；`--strict` 下 P2 也返回非零。
- CI 模板执行脚本编译和严格检查。
- hook 安装器复制最小运行时；`pre-commit` 快速检查，`pre-push` 严格检查。
- 已有非 vibe-spec hook 时拒绝覆盖。只有用户明确要求才使用 `--force`；原 hook 备份为 `.pre-vibe-spec`。

## 错误处理

- 先读 `findings`，再按 `next_actions` 修复。
- 解析冲突、重复 ID、非法状态、断裂引用和用户文件冲突都应停止自动写入。
- 多文件操作失败后，重新运行 `check --strict`，核对 spec、索引与交接事实是否一致。
