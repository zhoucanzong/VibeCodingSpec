---
name: vibe-spec
description: 跨 Agent 的规格驱动开发工作流。用于初始化项目规格、编写和继承 spec、维护 spec 生命周期、按 spec 实现、记录实验、规范数据存放和测试脚本、维护文件地图、审核实现结果、检查 spec/code drift，并帮助 Claude、Codex、Cursor 等工具按统一项目风格协作。
argument-hint: <需求> 或 init 或 spec <需求> 或 build <spec-id> 或 review <spec-id> 或 update <spec-id> 或 lifecycle <spec-id> 或 promote <spec-id> <state> 或 sync <spec-id> 或 retire <spec-id> 或 experiment <主题> 或 audit 或 status
allowed-tools: [Read, Write, Edit, MultiEdit, Bash, Grep, Glob, WebSearch, WebFetch]
---

# Vibe Spec

> 一句话：把项目意图、规格继承、实现记录、生命周期、实验数据、测试验证和审核结果变成可维护的跨 Agent 协作协议。

用户输入：`$ARGUMENTS`

## 命令路由

如果以 slash command 调用：

| 命令 | 作用 | 默认产物 |
|---|---|---|
| `/vibe-spec init` | 初始化项目规格工作区 | `.vibe-spec/` |
| `/vibe-spec spec <需求>` | 将需求转成可实现、可审核的 spec | 新 spec 或更新后的 spec |
| `/vibe-spec build <spec-id>` | 按已批准 spec 实现 | 代码变更与实现记录 |
| `/vibe-spec review <spec-id>` | 按验收标准审核实现 | 审核结论与修复项 |
| `/vibe-spec update <spec-id>` | 维护或演进已有 spec | spec 修订与变更记录 |
| `/vibe-spec lifecycle <spec-id>` | 查看 spec 生命周期状态和下一步 | 生命周期摘要 |
| `/vibe-spec promote <spec-id> <state>` | 按门禁推进 spec 状态 | 状态变更和证据 |
| `/vibe-spec sync <spec-id>` | 同步父 spec、决策或项目规则变化 | sync 记录 |
| `/vibe-spec retire <spec-id>` | 废弃、替代或归档 spec | 退役记录 |
| `/vibe-spec experiment <主题>` | 记录实验、benchmark、模型/Prompt 试验或数据检查 | 可复现实验记录 |
| `/vibe-spec audit` | 检查 spec/code drift | 审计报告 |
| `/vibe-spec status` | 汇总 spec 状态和下一步 | 项目交接摘要 |

如果用户自然语言调用，推断最接近的路径：

- “给这个项目建立规范” -> `init`
- “为这个功能写规格” -> `spec`
- “按这个 spec 实现” -> `build`
- “检查这个功能是否做完” -> `review`
- “把旧 spec 改一下” -> `update`
- “推进/回退这个 spec 状态” -> `promote`
- “父 spec 改了，同步一下” -> `sync`
- “这个功能废弃/被替代了” -> `retire`
- “记录这次 benchmark/实验/测试结果” -> `experiment`
- “看看项目哪里和规格不一致” -> `audit`

## 项目规范工作区

使用 `.vibe-spec/` 作为跨 Agent 的项目事实来源：

```text
.vibe-spec/
  PROJECT_SPEC.md     # 项目目标、用户、范围、边界
  AGENT_GUIDE.md      # Claude/Codex/Cursor 等 Agent 接手规则
  STYLE_GUIDE.md      # 工程、UI、命名、架构风格
  DECISIONS.md        # 长期有效的产品/技术决策
  LIFECYCLE.md        # spec 生命周期状态机、门禁和维护规则
  FILE_MAP.md         # 重要文件和目录分别是什么
  DATA_GUIDE.md       # 数据位置、schema、隐私、保留规则
  TESTING_GUIDE.md    # 测试命令、fixtures、验证脚本和期望
  EXPERIMENTS.md      # 实验、benchmark、评估和复现记录
  SPEC_INDEX.md       # 所有 spec 的状态、父子关系和下一步
  specs/              # 功能 spec
  reports/            # review/audit 报告
  scripts/            # 项目本地验证、迁移或维护脚本
```

运行 `init` 时创建缺失文件。已有文件不得覆盖；只补齐缺失结构或追加必要章节。

## 资源使用

按需读取资源，不要默认加载所有 reference：

| 资源 | 何时使用 |
|---|---|
| `scripts/init_vibe_spec.py` | 初始化目标项目的 `.vibe-spec/` |
| `assets/templates/FEATURE_SPEC.md` | 创建新功能 spec |
| `assets/templates/LIFECYCLE.md` | 初始化项目生命周期规则 |
| `assets/templates/REVIEW_REPORT.md` | 编写独立 review 报告 |
| `assets/templates/AUDIT_REPORT.md` | 编写 drift 审计报告 |
| `assets/templates/FILE_MAP.md` | 维护文件/目录说明 |
| `assets/templates/DATA_GUIDE.md` | 规范数据、fixtures、生成产物和隐私规则 |
| `assets/templates/TESTING_GUIDE.md` | 规范验证命令和测试脚本 |
| `assets/templates/EXPERIMENTS.md` | 记录可复现实验和 benchmark |
| `references/lifecycle-governance.md` | 执行状态推进、同步、退役、门禁检查 |
| `references/agent-compatibility.md` | 确保 Claude、Codex、Cursor 等工具都能接手 |
| `references/lifecycle.md` | 判断创建、实现、审核、替代或废弃 spec 的流程 |
| `references/review-checklist.md` | 执行 `/vibe-spec review <spec-id>` |
| `references/spec-drift.md` | 执行 `/vibe-spec audit` |
| `references/vibe-coding-field-notes.md` | 借鉴外部 vibe coding 经验时 |

## Agent 接手协议

改代码前，按顺序读取：

1. `.vibe-spec/AGENT_GUIDE.md`
2. `.vibe-spec/PROJECT_SPEC.md`
3. `.vibe-spec/SPEC_INDEX.md`
4. `.vibe-spec/LIFECYCLE.md`
5. `.vibe-spec/STYLE_GUIDE.md`
6. `.vibe-spec/DECISIONS.md`
7. `.vibe-spec/FILE_MAP.md`
8. 涉及数据、fixtures、实验或持久化时读 `.vibe-spec/DATA_GUIDE.md`
9. 运行或新增测试前读 `.vibe-spec/TESTING_GUIDE.md`
10. 评估方案、模型、prompt、数据、性能时读 `.vibe-spec/EXPERIMENTS.md`
11. 相关 spec
12. 相关代码、测试和相似实现

不要依赖某个工具的隐藏记忆。以仓库和 `.vibe-spec/` 为准。

## 状态值

状态值保持英文，便于脚本、表格和不同工具稳定识别：

- `idea`: 只有想法，还不构成可实现规格
- `draft`: 正在起草
- `ready_for_review`: 等待规格审核
- `approved`: 已批准，可以实现
- `in_progress`: 正在实现
- `implemented`: 代码完成，但未必验证通过
- `verification_failed`: 验证失败
- `verified`: 验证通过，但未必 review 完成
- `reviewed`: 审核通过
- `active`: 当前代表项目真实行为
- `needs_update`: 需求、代码或决策变化，需要更新
- `needs_sync`: 父 spec 或项目规则变化，需要同步
- `needs_changes`: 审核发现必须修复的问题
- `superseded`: 被新 spec 替代
- `deprecated`: 功能或规则被废弃
- `archived`: 历史保留，不参与日常决策

每次状态变化都要更新 `SPEC_INDEX.md`，并在目标 spec 的 `Lifecycle Log` 记录原因和证据。

## Spec 文件格式

功能 spec 放在 `.vibe-spec/specs/`，命名：

```text
YYYY-MM-DD-short-kebab-title.md
```

每个 spec 至少包含：

```markdown
---
spec_id: short-kebab-title
status: draft
parent: none
extends: []
supersedes: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
owner_agent: unspecified
---

# Spec: 标题

## Summary
## Context
## Goals
## Non-Goals
## Inherits From
## Adds
## Overrides
## Requirements
## Acceptance Criteria
## Implementation Notes
## Verification Plan
## Review Notes
## Lifecycle Log
## Changelog
```

Spec 要具体到另一个 Agent 可以不靠猜测继续实现。不要把 spec 写成长篇散文。

## 生命周期治理

Spec 是长期资产，不是一次性计划。执行生命周期相关操作前读取 `references/lifecycle-governance.md`。

核心状态路径：

```text
idea -> draft -> ready_for_review -> approved -> in_progress
-> implemented -> verified -> reviewed -> active
```

维护路径：

```text
active -> needs_update -> draft
active -> needs_sync -> draft
active -> superseded -> archived
active -> deprecated -> archived
implemented -> verification_failed -> in_progress
reviewed -> needs_changes -> in_progress
```

禁止静默跳过关键门禁：

- 不要把 `draft` 直接当成 `implemented`。
- 不要把 `implemented` 直接当成 `active`。
- 不要在没有记录原因的情况下从 `active` 改成 `deprecated` 或 `superseded`。
- 用户明确要求快速实现时可以跳过部分门禁，但必须在 `Lifecycle Log` 和最终回复中记录风险。

## 继承规则

当 spec 继承或扩展另一个 spec：

- 在 `parent` 或 `extends` 中列出父 spec。
- 默认继承父 spec 的目标、约束、风格规则和验收标准。
- 新增行为写入 `Adds`。
- 改变继承行为写入 `Overrides`。
- 不得静默废除父规则。
- 父 spec 更新后，子 spec 标记为 `needs_sync`，直到完成同步审核。
- 新 spec 替代旧 spec 时，新 spec 填 `supersedes`，旧 spec 标记为 `superseded`。

## 项目记忆维护

日常工作中同步维护这些文件：

- 添加、删除、移动、改职责的重要文件或目录时，更新 `FILE_MAP.md`。
- 新增数据集、fixtures、生成产物、schema、导出文件或敏感数据存放时，更新 `DATA_GUIDE.md`。
- 发现、新增、重命名或改变测试命令、验证脚本、fixtures、手动验证流程时，更新 `TESTING_GUIDE.md`。
- 运行 benchmark、模型评估、prompt 试验、数据检查、性能测试或探索性对比时，更新 `EXPERIMENTS.md`。
- `.vibe-spec/scripts/` 只放支持 spec、测试、审计、迁移或复现的项目本地脚本；产品代码脚本应放回项目自身脚本目录。
- 在实现记录和最终回复中说明相关项目记忆更新。

## 默认工作流

### Init

目标：让仓库可以被任何 Agent 接手。

1. 扫描项目结构和技术栈。
2. 运行 `scripts/init_vibe_spec.py <target-repo>`。
3. 从仓库中填充明显的项目目标、文件地图、测试命令、数据位置。
4. 不确定的信息写 `TBD`，不要编造。
5. 更新 `SPEC_INDEX.md`。
6. 汇报已初始化内容和仍需用户确认的问题。

### Spec

目标：把需求变成可实现、可审核、可维护的 spec。

1. 读取 `references/lifecycle.md` 和 `references/lifecycle-governance.md`。
2. 读取项目规范文件。
3. 查找相关 spec 和代码。
4. 判断是创建、继承、更新还是替代 spec。
5. 只有涉及产品方向、数据模型、权限、支付、安全、破坏性行为或明显互斥解释时才打断用户。
6. 写清 goals、non-goals、requirements、acceptance criteria、verification plan。
7. 更新 `SPEC_INDEX.md` 和 `Lifecycle Log`。

### Build

目标：按 spec 实现，并保持项目风格。

1. 读取项目规范文件和目标 spec。
2. 确认 spec 为 `approved`；若用户要求实现草稿，记录跳过门禁的风险。
3. 将状态推进到 `in_progress`。
4. 先查找现有模式，再改代码。
5. 做满足验收标准的最小完整实现。
6. 更新 `Implementation Notes`、`FILE_MAP.md`、`DATA_GUIDE.md`、`TESTING_GUIDE.md` 或 `EXPERIMENTS.md`。
7. 执行验证计划或最接近的现有测试。
8. 只有记录验证证据后才推进到 `implemented` 或 `verified`。

### Review

目标：判断实现是否满足 spec。

1. 读取 `references/review-checklist.md`。
2. 读取目标 spec、实现记录和变更代码。
3. 检查每条验收标准。
4. 检查继承约束和 overrides。
5. 查找 spec 外行为。
6. 检查验证证据。
7. 在 `Review Notes` 写结论：`Pass`、`Pass with Notes`、`Needs Work` 或 `Blocked`。
8. 重要 review 另存到 `.vibe-spec/reports/`。
9. 通过后推进到 `reviewed` 或 `active`；存在必须修复项时标记 `needs_changes`。

### Lifecycle / Promote / Sync / Retire

目标：规范化维护 spec 的状态变化。

1. 读取 `references/lifecycle-governance.md`。
2. 检查目标状态对应的 gate。
3. 确认需要更新的 spec、父子 spec、`SPEC_INDEX.md` 和项目记忆文件。
4. 写入 `Lifecycle Log`。
5. 只在证据齐全时推进状态。

### Experiment

目标：保留探索和评估工作的可复现性。

1. 读取 `.vibe-spec/EXPERIMENTS.md`、`.vibe-spec/DATA_GUIDE.md`、`.vibe-spec/TESTING_GUIDE.md`。
2. 记录 hypothesis、inputs、数据或 fixture 版本、命令、环境、指标、结果。
3. 只把生成产物存到批准路径。
4. 记录实验是否影响 spec、decision 或实现计划。
5. 区分 raw data、derived data 和 reports。

### Audit

目标：发现 spec 与代码、测试、数据、项目记忆之间的漂移。

读取 `references/spec-drift.md`，检查：

- 已批准但没有实现的 spec。
- 已实现但没有 review 的 spec。
- 已 review 但验收标准与代码行为不一致的 spec。
- 有代码行为但没有 spec 的功能。
- 仍被 active spec 引用的 deprecated/superseded spec。
- 父 spec 更新后未同步的子 spec。
- 违反 `DECISIONS.md`、`STYLE_GUIDE.md`、`DATA_GUIDE.md` 或 `TESTING_GUIDE.md` 的实现。
- `FILE_MAP.md` 与真实文件结构不一致。

重要审计报告保存到 `.vibe-spec/reports/`。

### Status

目标：生成可以贴给另一个 Agent 的交接摘要。

1. 读取 `SPEC_INDEX.md`。
2. 按状态统计 spec。
3. 找出 `needs_changes`、`needs_sync`、`needs_update`、`verification_failed` 和长期停滞项。
4. 列出最值得做的下一步。
5. 回复保持简短。

## 工程规则

- 先读项目，再改代码。
- 优先复用现有项目模式。
- 改动范围绑定到当前 spec。
- 不做无关重构。
- 不无故引入依赖。
- 保留用户已有改动和 git 历史。
- 实现中发现需求或技术决策变化时，先更新 spec 或 `DECISIONS.md`。
- 测试、构建、lint、截图、手动复现步骤都可以作为验证证据。
- 无法验证时记录原因和剩余风险。

## 最终回复格式

完成实现时：

```markdown
完成。

Spec:
- `<spec-id>` -> `<state>`

改动:
- ...

验证:
- ...

说明:
- ...
```

做 review 时，先给 verdict 和必须修复项。

做 audit 时，先列最高优先级 drift。
