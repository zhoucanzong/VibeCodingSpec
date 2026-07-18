---
name: vibe-spec
description: Use when 跨 Agent 或跨工具维护 coding 项目，需要初始化项目规范、理解代码层级、记录当前工作和未来计划、编写或继承 spec、按生命周期实现与审核、检查 spec/code drift，或让 Claude、Codex、Cursor 等工具持续接手同一仓库。
metadata:
  argument-hint: <需求> 或 init [profile] 或 context 或 handoff 或 roadmap 或 spec <需求> 或 build/review/promote/check/status <spec-id>
allowed-tools: [Read, Write, Edit, MultiEdit, Bash, Grep, Glob, WebSearch, WebFetch]
---

# Vibe Spec

`vibe-spec` 是 Agent-first 的跨工具项目治理 Skill。Agent 负责理解上下文、澄清意图、判断内容质量和协调审查；脚本只处理可确定的创建、校验、同步与汇总。脚本不能替代产品判断、工程判断或独立 review。

用户输入：`$ARGUMENTS`

## 核心约束

- 把仓库和 `.vibe-spec/` 作为唯一长期事实来源，不依赖某个工具的隐藏会话记忆。
- Markdown 是持久状态；JSON 仅用于命令即时输出。
- 先理解项目和活跃 spec，再修改代码。
- 不覆盖用户已有规则、代码或 Git hooks；无法安全合并时停止并说明冲突。
- 没有脚本时按本文和 references 手工完成等价流程。
- Claude 风格 slash command 与 Codex/其他 Agent 的自然语言调用必须得到相同行为。

## 命令路由

| 命令 | 目标 | 主要动作 |
|---|---|---|
| `init [profile]` | 初始化治理工作区 | 选择 profile/module、跨 Agent 入口、CI 和 hooks |
| `enable <module>` | 追加治理能力 | 幂等补齐模块，不删除已有内容 |
| `context` | 理解代码层级 | 核对 `FILE_MAP.md`，生成只读候选 |
| `handoff` | 维护当前工作 | 更新目标、活跃 spec、阻塞、验证和下一动作 |
| `roadmap` | 维护未来计划 | 更新 now/next/later/done，并关联 spec |
| `spec <需求>` | 创建或演进规格 | 澄清需求、继承关系、验收标准和验证计划 |
| `build <spec-id>` | 按批准规格实现 | 推进状态、实现、验证、记录项目记忆 |
| `review <spec-id>` | 审核实现 | 独立审查优先，记录 verdict 和 findings |
| `promote <spec-id> <state>` | 推进生命周期 | 检查合法状态和内容门禁，再同步日志与索引 |
| `sync <spec-id>` | 同步继承变化 | 标记 `needs_sync`，核对父子差异后重审 |
| `retire <spec-id>` | 替代或废弃规格 | 推进到 `superseded`/`deprecated`，最后归档 |
| `check [--strict]` | 自动健康检查 | 检查结构、索引、引用、证据和交接信息 |
| `status` | 汇总项目状态 | 汇总 spec、当前工作、阻塞与近期计划 |
| `experiment <主题>` | 记录可复现实验 | 保存输入、环境、命令、指标、结果和影响 |
| `audit` | 检查 drift | 对照 spec、代码、测试、数据和项目记忆 |

自然语言请求映射到最接近的命令。完整脚本参数和手工降级步骤见 `references/automation.md`。

## 固定接手协议

开始工作时先读取 `HANDOFF.md`，再按以下顺序建立上下文：

1. `.vibe-spec/HANDOFF.md`：当前目标、工作状态、阻塞、验证和下一动作。
2. `.vibe-spec/AGENT_GUIDE.md`：本项目的 Agent 行为规则。
3. `.vibe-spec/PROJECT_SPEC.md`：产品目标、范围和技术边界。
4. `.vibe-spec/SPEC_INDEX.md`、活跃 spec：正在进行的规格及依赖。
5. `.vibe-spec/ROADMAP.md`：now、next、later、done。
6. `.vibe-spec/STYLE_GUIDE.md`、`.vibe-spec/DECISIONS.md`：长期规范和决策。
7. `.vibe-spec/FILE_MAP.md`：代码层级、入口、目录和关键文件职责。
8. 与任务相关的 testing、data、security、release、migration、environment、observability 或 contracts guide。
9. 相关代码、测试和相似实现。

如果 `HANDOFF.md` 指向不存在的 spec、文件或命令，先报告 drift 并修复事实来源。不要默默猜测。

暂停、完成或切换 Agent 前更新 `HANDOFF.md`：记录当前状态、修改范围、最近验证、已知风险、阻塞和唯一明确的下一动作。代码层级变化时更新 `FILE_MAP.md`；未来优先级变化时更新 `ROADMAP.md`。

## Init 决策

用户未指定 profile 时，只询问会改变治理成本的选择：

| Profile | 默认模块 | 场景 |
|---|---|---|
| `minimal` | core | prototype、小项目、探索期 |
| `standard` | core、memory、testing、review | 常规应用 |
| `production` | 全部生产模块和 scripts | 有真实用户、CI、数据、auth、支付、迁移或发布流程 |

同时确认是否需要：

- `CLAUDE.md`、`AGENTS.md`、Cursor rule 等薄入口；它们只指向 `.vibe-spec/HANDOFF.md` 和 `AGENT_GUIDE.md`。
- GitHub Actions；仅显式选择时生成。
- Git hooks；仅显式选择时安装，已有非 vibe-spec hook 默认拒绝覆盖。

初始化后由 Agent 从仓库补齐项目摘要、代码入口、测试入口、当前工作和下一步。无法确认的信息写 `unknown` 并向用户确认，不编造。

## Spec 与继承

创建或修改 spec 前读取 `references/lifecycle.md` 和 `references/lifecycle-governance.md`。

- spec 文件名使用 `YYYY-MM-DD-short-kebab-title.md`，`spec_id` 长期稳定。
- `parent`/`extends` 声明继承来源；`Adds` 写新增行为；`Overrides` 显式写改变的父规则。
- 父 spec 或项目决策变化后，受影响子 spec 进入 `needs_sync`。
- 替代旧 spec 时，新 spec 写 `supersedes`，旧 spec 进入 `superseded`。
- Requirements、Acceptance Criteria 和 Verification Plan 必须具体到另一 Agent 无需猜测即可实现和验证。

主状态路径：

```text
idea -> draft -> ready_for_review -> approved -> in_progress
-> implemented -> verified -> reviewed -> active
```

不得把计划文字当成验证结果，不得把实现者结论当成 review，不得静默跳过门禁。紧急跳过门禁时，必须在 `Lifecycle Log`、`HANDOFF.md` 和最终回复中记录原因与风险。

## Build 工作流

1. 完成固定接手协议，确认目标 spec 为 `approved`。
2. 推进到 `in_progress`，记录 actor、reason 和 evidence。
3. 先查找项目已有模式，再做满足验收标准的最小完整实现。
4. 更新 `Implementation Notes`，列出代码路径、重要选择和偏差。
5. 同步 `FILE_MAP.md`、测试、数据、实验和相关生产 guide。
6. 执行 Verification Plan，记录命令、结果和失败项。
7. 推进到 `implemented`；只有存在通过证据时推进到 `verified`。
8. 强制进入 Post-Build Review。
9. 更新 `HANDOFF.md` 和 `ROADMAP.md`。

## Post-Build Review

实现完成后必须审核：

1. 使用 `prepare_review_context.py` 生成仅含 spec、diff 摘要、验证目标和相关文件的审查包。
2. 当前工具支持 subagent 时，启动独立 reviewer；不要传入实现者的 `Implementation Notes` 结论或已有 review 结论。
3. 当前工具不支持 subagent 时，按 `references/review-checklist.md` 自审，并在报告中标记 `mode: self`。
4. 使用 `create_review.py` 保存报告并回链 `Review Notes`。
5. reviewer 判定通过后才允许推进到 `reviewed`；存在阻塞问题时推进到 `needs_changes`。

改动超过 3 个文件，或涉及 auth、payment、security、privacy、migration、external API、P0/P1 drift、`reviewed`/`active` 推进时，要求独立 subagent。当前环境没有 subagent 时，明确记录限制，不得伪造独立审查。

## 项目记忆

| 变化 | 必须维护 |
|---|---|
| 重要文件、目录、职责或依赖层级 | `FILE_MAP.md` |
| 产品或技术长期决策 | `DECISIONS.md` |
| 测试命令、fixtures、验证方式 | `TESTING_GUIDE.md` |
| 数据、schema、隐私、生成产物 | `DATA_GUIDE.md` |
| benchmark、模型、prompt、性能实验 | `EXPERIMENTS.md` |
| API、事件或外部集成 | `CONTRACTS.md` |
| 发布、迁移、环境或可观测性 | 对应 production guide |

## 资源路由

- 自动命令、JSON、CI、hooks 和手工降级：`references/automation.md`
- 状态推进、同步、退役和门禁：`references/lifecycle-governance.md`
- spec 创建、继承和维护判断：`references/lifecycle.md`
- review 验收方法：`references/review-checklist.md`
- drift 审计：`references/spec-drift.md`
- Claude、Codex、Cursor 适配：`references/agent-compatibility.md`
- 数据、实验、测试和生产规范：读取 `.vibe-spec/MODULES.md` 中已启用模块对应模板。

不要默认加载所有 reference，只读取当前命令需要的内容。

## 完成门禁

声称完成前必须同时满足：

- 目标 spec 状态、Implementation Notes、验证证据和 Review Notes 一致。
- `SPEC_INDEX.md`、`HANDOFF.md`、`ROADMAP.md` 与当前工作一致。
- `check_vibe_spec.py --strict` 没有 P0/P1/P2，或明确记录无法修复的外部阻塞。
- 已运行项目测试和相关手动验证；未运行项明确说明。
- 最终回复先给结论，再列 spec 状态、主要改动、验证、审查方式和剩余风险。
