# 发布指南

用于记录发布、回滚、灰度和发布后验证流程。

## 环境

| 环境 | 用途 | 部署方式 | 验证方式 |
|---|---|---|---|
| dev | TBD | TBD | TBD |
| staging | TBD | TBD | TBD |
| production | TBD | TBD | TBD |

## 发布前检查

- [ ] 目标 spec 状态至少为 `verified`。
- [ ] Review 已完成，或已记录跳过 review 的原因。
- [ ] 必要测试、build、lint 已运行。
- [ ] 迁移、配置、feature flag 影响已检查。
- [ ] 回滚方案已记录。

## Rollout

| 步骤 | 操作 | 验证 | 回滚条件 |
|---|---|---|---|
| 1 | TBD | TBD | TBD |

## 回滚

- 回滚命令/流程：TBD
- 数据回滚策略：TBD
- Feature flag / kill switch：TBD

## 发布后验证

- 观察窗口：TBD
- 关键指标：TBD
- 告警链接：TBD
