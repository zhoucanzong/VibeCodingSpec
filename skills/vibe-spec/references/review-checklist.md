# Review 清单

用于 `/vibe-spec review <spec-id>`。

## 结论值

- `Pass`: 实现满足 spec，验证证据充分。
- `Pass with Notes`: 可以接受，但有非阻塞后续项。
- `Needs Work`: 仍有必须修复项。
- `Blocked`: 缺少权限、数据或需求信息，无法得出结论。

## 验收标准

- 每条 Acceptance Criteria 都被检查。
- 每条通过项都有证据。
- 未检查项说明原因。
- 实现中新增的标准已同步回 spec。

## 继承关系

- 父 spec 约束仍然适用。
- Overrides 明确。
- 没有静默删除继承行为。
- 父行为变化时，子 spec 已标记 `needs_sync`。

## 代码质量

- 实现遵循现有项目模式。
- 没混入无关重构。
- 新抽象有明确理由。
- 相关场景覆盖 error、loading、empty、edge states。
- 输入校验和权限边界处理在合适位置。

## 验证证据

- 可用时运行已有测试。
- 相关时运行 build 或 lint。
- 手动验证步骤足够具体，可复现。
- UI 工作尽量保留截图或浏览器检查记录。
- 跳过的检查说明原因和风险。

## 文档同步

- Implementation Notes 列出改动文件和理由。
- 新决策写入 `DECISIONS.md`。
- `SPEC_INDEX.md` 状态和下一步最新。
- Superseded 或 deprecated spec 标记一致。
- `FILE_MAP.md`、`DATA_GUIDE.md`、`TESTING_GUIDE.md`、`EXPERIMENTS.md` 已按需更新。

## Review 输出格式

```markdown
## Review Notes

### 结论

Pass | Pass with Notes | Needs Work | Blocked

### 验收清单

- [x] Criterion - evidence
- [ ] Criterion - required fix

### 问题

| Severity | Issue | Evidence | Required Fix |
|---|---|---|---|

### 验证证据

- Command or manual check: result

### 后续动作

- Non-blocking item
```
