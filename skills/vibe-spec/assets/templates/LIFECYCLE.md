# Spec 生命周期

## 核心路径

```text
idea -> draft -> ready_for_review -> approved -> in_progress
-> implemented -> verified -> reviewed -> active
```

## 维护路径

```text
active -> needs_update -> draft
active -> needs_sync -> draft
active -> superseded -> archived
active -> deprecated -> archived
implemented -> verification_failed -> in_progress
reviewed -> needs_changes -> in_progress
```

## 门禁

### Draft Gate

- [ ] 有 summary、context、goals、non-goals。
- [ ] 验收标准可检查。
- [ ] 验证计划可执行。
- [ ] 继承关系和 overrides 明确。

### Approval Gate

- [ ] 没有未解决的关键问题。
- [ ] 依赖 spec 没有处于 `needs_sync`。
- [ ] 范围、非目标和验收标准明确。

### Implementation Gate

- [ ] 状态为 `approved`，或已记录跳过审批的原因。
- [ ] 已查找现有实现模式。
- [ ] 实现范围绑定到当前 spec。

### Verification Gate

- [ ] 已记录执行的命令或手动验证步骤。
- [ ] 失败项已记录。
- [ ] 无法验证的原因和风险已记录。

### Review Gate

- [ ] 每条 acceptance criteria 都有结论。
- [ ] 继承约束和 overrides 已检查。
- [ ] spec 外行为已记录。
- [ ] 必须修复项已进入 `needs_changes`。

### Active Gate

- [ ] 状态已到 `reviewed`。
- [ ] `SPEC_INDEX.md` 已更新。
- [ ] `FILE_MAP.md`、`DATA_GUIDE.md`、`TESTING_GUIDE.md`、`EXPERIMENTS.md` 已按需更新。
- [ ] 没有阻塞项。

## 生命周期日志格式

每个 spec 都应维护：

| 日期 | From | To | Actor | 原因 | 证据 |
|---|---|---|---|---|---|
| TBD | draft | approved | TBD | TBD | TBD |
