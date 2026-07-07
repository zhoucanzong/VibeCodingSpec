# 模块配置

用于记录当前项目启用了哪些 vibe-spec 治理模块。

## Profile

TBD

## Enabled Modules

| 模块 | 是否启用 | 用途 | 备注 |
|---|---|---|---|
| core | yes | 项目规格、生命周期、Agent 接手和 spec 索引 | 必选 |
| memory | TBD | 决策记录和文件地图 | standard 默认启用 |
| testing | TBD | 测试命令、fixtures 和验证脚本 | standard 默认启用 |
| review | TBD | review/audit 报告模板 | standard 默认启用 |
| data | TBD | 数据、schema、隐私和生成产物 | production 默认启用 |
| experiments | TBD | 实验、benchmark 和评估记录 | production 默认启用 |
| security | TBD | 安全和隐私审查 | production 默认启用 |
| release | TBD | 发布、回滚和发布后验证 | production 默认启用 |
| migration | TBD | 数据库迁移和 backfill | production 默认启用 |
| environment | TBD | 环境变量和配置 | production 默认启用 |
| observability | TBD | 日志、指标、告警和事故观察 | production 默认启用 |
| contracts | TBD | API/事件/外部集成契约 | production 默认启用 |
| scripts | TBD | `.vibe-spec/scripts/` 辅助脚本目录 | production 默认启用 |

## 维护规则

- 启用新模块时，把相关文件加入 `.vibe-spec/` 并更新本文件。
- 不建议自动删除已启用模块；如果不再使用，标记为 disabled 并说明原因。
- 高风险生产项目优先启用 security、release、migration、environment、observability。
