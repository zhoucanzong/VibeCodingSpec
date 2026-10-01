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

推进到 `verified` 前，在 Verification Plan 中写入实际执行结果：

```markdown
- Result: `python -m unittest` -> PASS (exit 0)
```

“测试应该 PASS”或“计划记录通过结果”等未来时态不构成证据。成功推进会生成新的 `verification_id`。

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

`create_review.py` 只接受 `verified` spec，并把报告绑定到当前 `verification_id`。重新验证后必须重新 review；同一 verification 的最后 verdict 决定是否可以推进到 `reviewed`。

不支持 subagent 时，按 `references/review-checklist.md` 自审，并使用 `--mode self` 记录限制。

## Check、CI 与 Hooks

```bash
scripts/check_vibe_spec.py <repo>
scripts/check_vibe_spec.py <repo> --strict --json
scripts/install_git_hooks.py <repo> --json
```

- 默认 P0/P1 返回非零；`--strict` 下 P2 也返回非零。
- CI 模板执行脚本编译和严格检查。
- hook 安装器把最小运行时放入 Git common dir；所有 linked worktree 共用 `pre-commit` 快速检查和 `pre-push` 严格检查。
- 已有非 vibe-spec hook 时拒绝覆盖。只有用户明确要求才使用 `--force`；原 hook 备份为 `.pre-vibe-spec`。

## Collaboration

```bash
python3 scripts/init_vibe_spec.py <repo> --profile standard --modules collaboration
python3 scripts/status_vibe_spec.py <repo> --json
python3 scripts/check_vibe_spec.py <repo> --strict --json
```

已有项目使用其当前 profile，追加模块保留之前启用的模块与记录。所有 profile 默认关闭 collaboration，用户要求主管接管时启用。TEAM.md 初次生成后的 unknown 会被严格检查标为待补齐。

旧部署脚本与当前 Skill 不同时，启用协作会提前报错。核对定制后加 `--refresh-runtime` 备份并升级，已有 `.pre-vibe-spec` 备份不会被覆盖；若已安装 hooks，按原安装授权重新运行安装器更新其 common-dir 运行时。

主管按 `references/collaboration.md` 及生成的 `collaboration/TEAM.md` 联系成员，使用模板维护 agents/tasks/messages。`status` 增加 collaboration 摘要及 findings；`check --strict` 检查主管、角色、握手回执、规范版本、任务归属、依赖、修改范围和验收回执。读写这些记录不需要常驻服务或厂商 SDK。

脚本只验证记录结构与一致性，消息投递、回执真实性、预算管理和工程验收仍由当前 Agent 通过实际宿主工具处理。没有通信能力时提供接入步骤；没有后台能力时不承诺离线持续管理。

## 错误处理

- 先读 `findings`，再按 `next_actions` 修复。
- 解析冲突、重复 ID、非法状态、断裂引用和用户文件冲突都应停止自动写入。
- 多文件操作失败后，重新运行 `check --strict`，核对 spec、索引与交接事实是否一致。
