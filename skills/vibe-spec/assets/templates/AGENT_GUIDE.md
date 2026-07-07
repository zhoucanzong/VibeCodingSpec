# Agent 接手指南

## 读取顺序

改代码前读取：

1. `.vibe-spec/PROJECT_SPEC.md`
2. `.vibe-spec/SPEC_INDEX.md`
3. `.vibe-spec/LIFECYCLE.md`
4. `.vibe-spec/STYLE_GUIDE.md`
5. `.vibe-spec/DECISIONS.md`
6. `.vibe-spec/FILE_MAP.md`
7. 涉及数据、fixtures、持久化或生成产物时读 `.vibe-spec/DATA_GUIDE.md`
8. 运行、新增或修改测试前读 `.vibe-spec/TESTING_GUIDE.md`
9. 做 benchmark、模型、prompt、数据或性能工作时读 `.vibe-spec/EXPERIMENTS.md`
10. 相关 spec
11. 相关代码和测试

## 跨 Agent 规则

- 把仓库和 `.vibe-spec/` 当成当前事实来源。
- 不依赖另一个工具或上一次会话的隐藏记忆。
- 保留用户已有改动。
- 实现范围绑定到当前 spec。
- 推进工作时更新 spec 状态、实现记录和生命周期日志。
- 标记 implemented、verified 或 reviewed 前记录验证证据。
- 重要文件或目录新增、删除、移动、职责变化时更新 `FILE_MAP.md`。
- 记录数据位置、fixtures 和生成产物到 `DATA_GUIDE.md`。
- 记录测试命令和项目本地验证脚本到 `TESTING_GUIDE.md`。
- 记录实验时写到 `EXPERIMENTS.md`，让下一个 Agent 可以复现。

## 什么时候询问用户

以下情况先问用户：

- 产品方向或用户行为存在多个合理解释。
- 数据库 schema、迁移或持久化数据会变化。
- 涉及认证、授权、支付、安全或隐私边界。
- 涉及删除、不可逆操作或大规模重写。
- 涉及外部服务契约。

其他情况可以基于项目上下文做合理假设，并把假设记录到 spec 或最终回复中。
