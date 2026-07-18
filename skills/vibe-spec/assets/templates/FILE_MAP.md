# 文件地图

用于帮助后续 Agent 理解项目中重要文件和目录的职责。

## 维护规则

- 创建重要文件或目录时添加记录。
- 文件职责变化时更新记录。
- 描述保持事实化、简短。
- 如果文件服务某个 spec，在表格中关联 spec。

## 仓库地图

| 路径 | 类型 | 用途 | 关联 Spec | 备注 |
|---|---|---|---|---|
| `README.md` | 文档 | 项目概览 | project | TBD |
| `.vibe-spec/` | 规格工作区 | 跨 Agent 项目记忆和流程状态 | vibe-spec | 由 vibe-spec 创建 |

## 代码层级

从项目入口到具体实现记录主要层级。可以运行 `refresh_context.py` 获取候选，再由 Agent 核对后更新。

| 层级 | 路径 | 职责 | 依赖方向 | 关联 Spec |
|---|---|---|---|---|
| 入口 | unknown | unknown | 向内依赖 | project |
| 领域/核心 | unknown | unknown | 不依赖 UI/基础设施细节 | project |
| 适配/基础设施 | unknown | unknown | 实现核心定义的契约 | project |
| 测试 | unknown | unknown | 验证公开行为 | project |

## 生成或临时路径

| 路径 | 用途 | 可删除? | 备注 |
|---|---|---:|---|
| TBD | TBD | TBD | TBD |
