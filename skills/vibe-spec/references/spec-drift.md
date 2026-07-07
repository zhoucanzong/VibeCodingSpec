# Spec Drift 审计

用于 `/vibe-spec audit`。

## Drift 类型

### Missing Implementation：缺少实现

Spec 是 `approved` 或 `in_progress`，但没有实现记录或对应代码变化。

### Missing Review：缺少审核

Spec 是 `implemented` 或 `verified`，但没有 review 结论。

### Untracked Behavior：未记录行为

代码中存在重要产品行为，但没有相关 spec。

### Stale Acceptance：验收标准过期

Acceptance Criteria 描述的行为已经与代码不一致。

### Inheritance Drift：继承漂移

父 spec 改了，但子 spec 没有 review 或标记 `needs_sync`。

### Decision Drift：决策漂移

代码或 spec 与 `DECISIONS.md` 冲突。

### Style Drift：风格漂移

实现反复违反 `STYLE_GUIDE.md` 或既有代码模式。

### Memory Drift：项目记忆漂移

`FILE_MAP.md`、`DATA_GUIDE.md`、`TESTING_GUIDE.md` 或 `EXPERIMENTS.md` 与真实项目状态不一致。

## 审计方法

1. 读取 `.vibe-spec/SPEC_INDEX.md`。
2. 扫描 `.vibe-spec/specs/` 的状态、父子关系、supersession 和 review notes。
3. 有 git 历史时检查近期变更。
4. 在代码中搜索 spec 里提到的功能。
5. 在 spec 中搜索 implementation notes 提到的代码路径。
6. 对比 `DECISIONS.md`、`STYLE_GUIDE.md`、`DATA_GUIDE.md`、`TESTING_GUIDE.md` 和近期改动。
7. 报告可行动问题。

## 优先级

- `P0`: 已发布行为违反关键 spec、安全、隐私、数据或支付规则。
- `P1`: active 功能行为与验收标准冲突。
- `P2`: spec 状态、review 证据、实现记录或项目记忆过期。
- `P3`: 低风险文档卫生问题。

## 审计输出

```markdown
# Vibe Spec Audit

## 结论

Healthy | Drift Found | Blocked

## 发现

| Severity | Type | Spec/File | Evidence | Action |
|---|---|---|---|---|

## 状态汇总

| State | Count |
|---|---:|

## 建议下一步

- ...
```
