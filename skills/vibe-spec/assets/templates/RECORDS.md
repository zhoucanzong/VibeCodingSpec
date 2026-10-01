# 工作记录与留存

## 四层事实

| 层次 | 内容与位置 | 维护规则 |
|---|---|---|
| 当前状态 | HANDOFF、任务与实验计划的状态字段、索引 | 精简、可接手；修改 HANDOFF 前完整快照旧版 |
| 过程记录 | 文档 Progress、Lifecycle Log、history/events、history/handoffs | 按时间追加，保留操作者、事件、证据、下一动作和原文档链接 |
| 正式结论 | 验收、review、实验结论、决策及其稳定 ID | 必须绑定实际证据；过程日志不代替验收或独立审查 |
| 原始产物 | 测试输出、实验 runs、输入版本、命令、环境、指标及产物 | 保留可追溯路径和版本；大型或敏感产物使用获准存储并记录校验值与访问限制 |

## 追加与检查点

- 旧日志、历史事件和快照不可覆盖或删除；撤销、更正另加条目，引用被更正记录的稳定 ID，说明原因和替代结论。
- 接单、计划批准、重要实验或测试、失败与阻塞、用户改令、实现完成、review、验收、暂停和交接均是重要检查点；及时留存，失败证据同样保留。
- `record_work.py TARGET RECORD --actor ACTOR --event EVENT --summary TEXT` 只追加过程记录，不自行改变任务状态或宣称完成；可重复传 `--evidence` 并提供 `--next-action`、`--json`。
- RECORD 是 `.vibe-spec/` 内已有 Markdown 相对路径，禁止路径逃逸、外部符号链接、模板和历史文件；Progress 链接不可覆盖的 `history/events/<uuid>.md`，事件反向链接原文档。
- HANDOFF 仅在有效内容变化时生成 `history/handoffs/<utc时间>-<uuid>.md` 完整旧版；相同输入不反复生成快照。历史和当前文档通过同一多文件写入操作保存，写入失败回滚，不留孤立历史。
- 同一目标的写入先取得 `record_lock(workspace, record)`；workspace 必须存在，record 可尚未创建。锁按规范化的工作区相对路径存于 `.locks/<sha256>.lock`，占用即失败，不等待、不强抢。所有相关写入方须遵守同一约定；实验创建依次锁定 EXPERIMENTS.md 与实验 PLAN.md。`.locks/` 是临时运行状态，不纳入 Git，不作为长期事实。
- 锁不支持嵌套获取同一目标。进程异常退出后，先核实锁内 PID 对应的写入者已结束，再人工清理残留锁并重试；不能仅按锁龄删除。

## 逻辑归档

- 归档是逻辑状态，文件留在原位，保留稳定 ID、证据、引用和历史；不得搬迁或删除文件来表示完成。
- collaboration task 只有 `status: accepted` 或 `status: cancelled` 才能设置 `archived: true`；同时填写非空 `archived_at`（UTC 时间）和 `archive_reason`。submitted 不等于 accepted。
- 实验 PLAN 只有 `status: completed` 或 `status: cancelled`，且该实验所有 runs 均已终态，才能设置 `archived: true`；同时填写 `archived_at` 和 `archive_reason`。取消计划不能掩盖仍在进行的 run。
- 归档不复用、不改写 task_id、experiment_id、run_id 等稳定 ID。纠正归档或恢复工作时新增过程条目说明原因，并遵守对应生命周期规则。

## Git 授权

工作记录落盘不等于 Git 提交。Git commit 与 push 遵循用户在当前任务中的既有授权，无需重复询问已授权操作；没有实际执行并验证成功，不得自称“已提交”“已推送”。留存脚本不代用户执行提交或推送。
