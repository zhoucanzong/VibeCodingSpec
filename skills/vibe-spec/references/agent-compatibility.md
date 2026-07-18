# 跨 Agent 兼容

当同一项目可能被 Claude、Codex、Cursor 或 IDE Agent 维护时，使用这些规则。

## 可移植指令

- 把长期事实写入 `.vibe-spec/`，不要依赖某个工具的隐藏记忆。
- 优先使用 Markdown，而不是只有某个工具能解析的隐藏配置。
- 命令既要能被 slash command 理解，也要能被自然语言触发。
- frontmatter 可以作为工具提示，但关键行为必须写在正文。
- Agent 在不询问用户的情况下做出的假设，要写入 spec 或实现记录。
- 所有工具先读 `.vibe-spec/HANDOFF.md`，再读 `.vibe-spec/AGENT_GUIDE.md`。
- 代码层级以 `FILE_MAP.md` 为准，当前工作以 `HANDOFF.md` 为准，未来计划以 `ROADMAP.md` 为准。

## Claude 友好约定

- `argument-hint` 保持简短、命令式。
- `allowed-tools` 作为 Claude 风格 skill runner 的提示。
- 明确写出 `/vibe-spec build <spec-id>` 这类路由。

## Codex 友好约定

- 触发条件写进 `description`。
- 必须遵守的行为写进 Markdown 正文。
- 不要求用户必须使用 slash command。
- 以仓库文件和验证证据为准，不依赖对话记忆。
- 使用 `agents/openai.yaml` 提供 UI 元数据；核心规则仍保留在 `SKILL.md`。

## Cursor 与 IDE Agent

- 把 `.vibe-spec/HANDOFF.md` 作为第一接手入口，把 `AGENT_GUIDE.md` 作为行为规则。
- 在实现记录中把 spec 关联到具体代码路径。
- 保持 `SPEC_INDEX.md` 最新，让 Agent 不必扫描所有文件也能找到当前工作。

## 交接纪律

每个 Agent 离开前应留下：

- 当前 spec 状态。
- 修改过的文件。
- 验证命令和结果。
- 已知风险或跳过的检查。
- 未完成工作时的下一步。
- `ROADMAP.md` 中 now/next/later 的变化。
