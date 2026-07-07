# Spec 流程指南

用于创建、实现、更新、审核或退役 spec。

## 什么时候创建 spec

以下情况创建新 spec：

- 用户提出新功能、新流程、新集成或重要 bug fix。
- 工作有值得追踪的验收标准。
- 实现会影响多个文件或未来行为。
- 多个 Agent 可能在不同时间接手。

以下情况更新已有 spec：

- 请求是对已有行为的 refinement。
- 工作改变了已接受的需求。
- review 发现缺口，需要补充或修正。

以下情况通常不必创建 spec：

- 很小的文案修改。
- 纯机械格式化。
- 不改变产品行为的一行内部修复。

## Approval

Spec 可以进入 `approved` 的条件：

- Goals 和 Non-Goals 清楚。
- Acceptance Criteria 可检查。
- Inheritance 和 Overrides 明确。
- Verification Plan 对当前仓库现实可执行。

如果用户明确要求未批准就实现，可以继续，但要在 `Lifecycle Log` 和最终回复中记录风险。

## Implementation

实现过程中：

- 将 spec 标记为 `in_progress`。
- 改动范围绑定到 spec。
- 随事实更新 Implementation Notes。
- 如果实现需要 spec 未覆盖的新行为，先更新 spec。

只有满足以下条件才标记 `implemented`：

- 代码改动完成。
- 每条验收标准能对应到实现记录。
- 验证证据已记录，或无法验证的原因已记录。

## Review

只有满足以下条件才标记 `reviewed`：

- 所有必须验收标准通过。
- 继承约束仍然成立。
- 验证证据足够。
- 没有必须修复项。

实现接近完成但仍有阻塞问题时使用 `needs_changes`。
缺少权限、数据或需求不清导致无法判断时，在 Review Notes 中写 `Blocked`。

## Supersession 与 Deprecation

- 新 spec 替代旧 spec 时，旧 spec 用 `superseded`。
- 行为被有意移除且没有替代时，用 `deprecated`。
- 历史保留、不参与日常决策时，用 `archived`。

必须同步更新：

- 旧 spec 状态。
- 新 spec 的 `supersedes` 字段。
- `SPEC_INDEX.md`。
- 继承旧行为的子 spec。
