# 实验索引与记录

用于记录 benchmark、模型评估、prompt 试验、数据检查、性能测试和探索性对比，保证后续 Agent 可以复现。

## 新实验的记录协议

- 本页保留简短索引，详细记录存 `experiments/<experiment_id>/PLAN.md`、`runs/<run_id>.md`、`conclusions/<conclusion_id>.md`。
- 先明确问题、假设、基线/对照、固定/变化条件、数据切分、重复方式、指标、事先判定标准、预算和停止条件；每次运行冻结当时计划快照。
- 开始前写实际代码提交与未提交补丁、数据版本、模型/提示词/参数、种子、环境和命令，执行后写时间、退出码、实测指标、异常和产物。
- 重跑新建运行 ID；失败、中断和负结果同样保留。假设、观测和解释分开，不把计划文字当结果。
- 每版结论绑定运行记录 SHA256；结论 reviewed 要有绑定其内容的真实审查报告。completed 仅表示执行结束，不代表假设成立。
- 产物默认可放 `artifacts/experiments/<experiment_id>/<run_id>/`，优先沿用项目数据规范。大文件使用约定外部存储；文档保存位置、版本、校验值。
- 更新/纠错、关键检查点与逻辑归档按 RECORDS.md；旧记录不覆盖、不搬移断链。
- 模板位于 `experiments/templates/`，脚本 `create_experiment.py` 只生成草稿和证据关联，实际实验由 Agent 执行。

## 实验日志

| 日期 | 实验 ID | 假设 | 输入/数据 | 命令/方法 | 指标 | 结果 | 后续动作 |
|---|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

## 历史兼容样例

旧格式记录原样保留；新增实验采用上述独立计划、逐次运行与结论模板。

````markdown
## YYYY-MM-DD-short-experiment-id

### 假设

TBD

### 背景

TBD

### 输入

- 数据/fixtures:
- Spec:
- Code version:
- Environment:

### 方法

```text
command or procedure
```

### 指标

- TBD

### 结果

TBD

### 产物

- TBD

### 对决策的影响

- Spec changes:
- Decision log changes:
- Implementation changes:

### 后续动作

- TBD
````
