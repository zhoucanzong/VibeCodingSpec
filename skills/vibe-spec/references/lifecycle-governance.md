# 生命周期治理

Spec 是项目长期资产。任何状态推进、同步、退役都必须留下原因和证据。

## 状态转换

推荐主路径：

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

## Promotion Gate

推进状态前检查：

| 目标状态 | 必须满足 |
|---|---|
| `draft` | 有明确问题、背景或需求来源 |
| `ready_for_review` | 有 goals、non-goals、requirements、acceptance criteria、verification plan |
| `approved` | 关键问题已解决，继承关系明确，验收标准可检查 |
| `in_progress` | 已批准，或用户明确要求跳过审批且已记录风险 |
| `implemented` | 代码完成，Implementation Notes 已记录改动文件和理由 |
| `verified` | 验证计划已执行，证据已记录 |
| `reviewed` | Review Notes 给出通过结论，无必须修复项 |
| `active` | 已 reviewed，SPEC_INDEX 和相关项目记忆已更新 |
| `needs_update` | 需求、代码、实验或决策变化导致 spec 不再准确 |
| `needs_sync` | 父 spec、项目规则或决策变化影响当前 spec |
| `superseded` | 有新 spec 明确替代，并填写 `supersedes` |
| `deprecated` | 行为被有意废弃，影响和迁移路径已记录 |
| `archived` | 不再参与日常决策，仅历史保留 |

## Lifecycle Log

每次状态变化都写入目标 spec：

```markdown
| 日期 | From | To | Actor | 原因 | 证据 |
|---|---|---|---|---|---|
```

证据可以是：

- 用户确认。
- review 结论。
- 测试命令和结果。
- audit finding。
- commit、PR、文件路径。
- 实验记录。

## 维护触发器

以下事件必须检查 spec 是否需要 `needs_update` 或 `needs_sync`：

- 相关代码被改动。
- 父 spec 更新。
- `DECISIONS.md` 改变。
- `STYLE_GUIDE.md`、`DATA_GUIDE.md` 或 `TESTING_GUIDE.md` 改变。
- 测试失败说明 spec 不准确。
- 用户修改需求。
- 实验结果推翻原方案。
- audit 发现 drift。
- 文件结构变化影响 `FILE_MAP.md`。
- 数据 schema 或 fixture 变化。

## Sync 规则

父 spec 变化后：

1. 找到所有 child specs。
2. 将受影响 child 标记为 `needs_sync`。
3. 对每个 child 判断：
   - 继承新规则。
   - 显式 override 新规则。
   - 被新 spec supersede。
   - 被 deprecated。
4. 更新 `SPEC_INDEX.md` 和 `Lifecycle Log`。

## Retire 规则

退役 spec 前确认：

- 退役原因清楚。
- 替代 spec 或废弃影响已记录。
- 相关 child specs 已处理。
- 相关测试、数据、文件地图和文档已更新。
- 用户可见行为变化已写入 changelog 或 spec。
