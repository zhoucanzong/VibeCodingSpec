# 实验与证据

用户要求模型开展实验时，启用 experiments 并读取项目 EXPERIMENTS.md、DATA_GUIDE（若存在）、相关 Spec 与 RECORDS.md。使用既有实验框架、命令和数据约定，避免平行建立另一套实验事实。

## Agent 工作顺序

1. 创建计划：明确问题和可证伪假设、基线/对照、变量、数据切分、重复运行方案、指标、决策标准、预算/停止条件。没有用户给出的数值时做有理由的设计并记录，不能事后改阈值以迁就结果。
2. 创建 run：每次启动一个新 ID，脚本冻结当前计划为 `plans/<sha256>.md`。在真正运行前填代码提交、未提交 patch 路径、数据版本/校验值、模型和提示词/参数、种子、环境、命令。配置中区分计划值和最终使用值。
3. 实际执行：使用授权的计算资源。把状态从 planned 改 running，结束后填 completed / failed / interrupted，分别记录开始/结束时间、退出码、实际指标、观测与产物。completed 要求 exit_code=0；实验指标变差不等于命令失败。中断未知退出码保持 unknown 并解释。异步任务在未读取最终结果前保持 running。
4. 保存证据：Artifacts 表中填写仓库相对路径或持久 https/s3/gs URI、SHA256、用途；本地路径不得越出仓库。未提交补丁也作为产物登记。表中路径含 `|` 时先改为可表示的稳定路径。不把数据凭据写入文档。没有适用模型/种子时写 not_applicable 并解释；没有指标的失败运行写 not_measured 并解释。
5. 形成结论：对已终止的运行创建新的 conclusion ID。脚本自动记录当前全部终态 run 的文件摘要；若还有 planned/running，先结束或等待，不能声称整个实验已完成。尚未执行的 planned 运行取消时记 cancelled，started/exit_code 保留 unknown，ended 写取消时间，Observations 写原因；已经启动后停止才记 interrupted。比较基线与实验组、重复运行差异/不确定性、失败和负结果，写清局限。
6. 审阅与决策：主线负责人检查设计和证据；重要产品/研究结论交独立 reviewer。记录 reviewer、review_mode=independent/self、review_evidence（仓库内报告路径）和 Review 正文。独立审阅者不能是 author；无独立能力明确 self。状态 reviewed 不自动意味着假设被支持；decision 可为 adopt/reject/inconclusive。主管再同步 Spec、DECISIONS、ROADMAP 或后续任务。

审阅报告使用 `experiments/templates/review.md`，frontmatter 写 experiment_id、conclusion_id、conclusion_sha256、reviewer、review_mode、verdict=pass/changes。Findings 记录实际问题或“未发现阻塞问题”及核验范围；Assessment 写设计、数据/基线公平性、重复运行、失败与负结果、指标产物、局限及决策的评估。模板占位说明不算证据。完成结论正文与审阅身份填写后，用 `create_experiment.py <repo> <experiment_id> --kind digest --record-id <conclusion_id> --json` 计算摘要，reviewer 对照实际内容后写入报告；摘要排除 status/review_evidence，其他内容变化均使旧审阅失效。`review_evidence` 使用仓库相对路径（例如 `.vibe-spec/reports/EXP-001-CON-001.md`）。

## 留存与更新

计划/运行状态可在执行期间更新。创建结论时锁定所有引用 run，把完整原文冻结为 `evidence/<run_id>/<sha256>.md`，Run Evidence 表保存 Run ID、SHA256、Snapshot 三列；快照不得编辑。终态记录发现错误时先用 record_work 留原因，再纠正并新建、重新审阅结论，通过 supersedes 替代旧结论；历史结论继续核验原快照，未被有效新结论替代的旧结论仍报告 drift。新增运行后旧结论只代表旧证据集；要结束整个实验，必须有覆盖当前全部终态 runs 的当前有效 reviewed 结论。结论正文改变也必须重新审核，不能沿用旧 review。

PLAN 状态 planned/running/completed/cancelled；CONCLUSION 状态 draft/reviewed。逻辑归档使用 PLAN 的 archived=true、archived_at、archive_reason，不搬文件、不删除原始产物。只有 completed/cancelled 且没有 planned/running 的 run 才归档；cancelled 要在计划 Progress 解释原因。旧格式的 EXPERIMENTS.md 保留，Agent 增量补入新索引和协议链接，不把历史记录覆盖成模板。

## 脚本

```bash
python3 scripts/create_experiment.py <repo> EXP-001 --kind plan --title "检索策略对比" --owner researcher --spec project
python3 scripts/create_experiment.py <repo> EXP-001 --kind run --record-id RUN-001 --owner researcher
python3 scripts/create_experiment.py <repo> EXP-001 --kind conclusion --record-id CON-001 --owner research-lead
python3 scripts/check_vibe_spec.py <repo> --strict --verify-artifacts --json
```

创建拒绝覆盖已有 ID；创建草稿不代表已执行/已审阅。默认 check 检查字段、引用、计划快照和结论绑定、本地产物存在性；`--verify-artifacts` 额外流式重算本地产物哈希，可能读取大文件。外部 URI 不自动联网下载，校验结果会标记未核验，需要 Agent 通过实际存储工具验证后在记录中保留证据。

旧项目运行 init 补齐新模板/RECORDS，已有部署脚本用 `--refresh-runtime` 备份升级；有 Git hooks 时刷新其 common-dir 运行时。status 动态扫描实验记录，EXPERIMENTS.md 的问题和结论摘要由 Agent 维护。
