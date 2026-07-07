# 测试指南

用于让不同 Agent 能复现验证过程。

## 标准命令

| 目的 | 命令 | 何时运行 | 备注 |
|---|---|---|---|
| 安装依赖 | TBD | 新 checkout | TBD |
| 单元测试 | TBD | 逻辑变更 | TBD |
| 集成测试 | TBD | API/数据变更 | TBD |
| Lint | TBD | review 前 | TBD |
| Build | TBD | 标记 implemented 前 | TBD |

## 测试脚本

项目本地测试或验证脚本应放在：

- 既有项目 test/script 目录。
- `.vibe-spec/scripts/`，仅用于不属于产品代码的 spec 工作流辅助脚本。

每个脚本应记录：

- 用途。
- 输入。
- 输出。
- 必需环境变量。
- 示例命令。

## Fixtures

| 路径 | 用途 | 关联 Spec | 备注 |
|---|---|---|---|
| TBD | TBD | TBD | TBD |

## 手动验证

只有自动化覆盖不足时使用手动验证。记录具体步骤、预期结果、实际结果和环境。

## 视觉验证

UI 工作记录 viewport、浏览器、路由、截图位置，以及已知视觉风险。
