# Vibe Coding 经验沉淀

这些原则来自对公开 vibe coding / AI coding agent 经验的整理。使用时把它们转成项目内的 spec、测试、review 和生命周期规则，不要当作口号。

## 可吸收原则

### 1. 先让 Agent 理解边界，再让它写代码

好的 vibe coding 不是直接让模型“随便写”，而是先给清晰上下文：目标、约束、非目标、现有模式、验收标准。`vibe-spec` 用 `PROJECT_SPEC.md`、`STYLE_GUIDE.md`、`SPEC_INDEX.md` 和功能 spec 承载这些上下文。

### 2. 把 prompt 变成 living spec

一次性 prompt 很容易丢失。把需求、假设、验收标准、实现记录和 review 证据写进 spec，后续 Agent 才能接手。

### 3. 小步实现，小步验证

大型模糊请求容易产生不可审查的大改动。优先把需求拆成可验收 spec，每次只推进一个明确状态。

### 4. 保留验证证据

“看起来能跑”不算完成。测试、build、lint、截图、手动步骤、实验结果都应写入 spec 或报告。

### 5. Review 要独立于实现叙事

实现者说完成不等于完成。Review 应逐条对照 Acceptance Criteria、继承规则和验证证据。

### 6. 记录文件、数据和实验

AI Agent 容易忘记临时数据、脚本和实验结果。`FILE_MAP.md`、`DATA_GUIDE.md`、`TESTING_GUIDE.md`、`EXPERIMENTS.md` 是为了把这些“隐性上下文”显性化。

### 7. 防止 spec/code drift

代码会变，spec 也必须变。Audit 要检查未实现 spec、未 review 实现、未记录代码行为、过期验收标准、父子 spec 不同步。

## 融入方式

- 新需求：先写 spec，再实现。
- 模糊需求：先进入 `draft`，只问关键问题。
- 快速试验：写入 `EXPERIMENTS.md`，不要直接污染 active spec。
- 试验成功：更新 spec、decision 或 implementation plan。
- 试验失败：记录结果，避免后续 Agent 重复走同一条路。
- 实现完成：进入 `implemented`，不是直接 `active`。
- 验证通过：进入 `verified`。
- Review 通过：进入 `reviewed` 或 `active`。

## 来源与吸收点

- Martin Fowler 的 SDD 文章把 spec 定义为结构化、面向行为、用于指导 AI coding agents 的自然语言 artifact；本 skill 因此把 spec 设计成可继承、可审核、可维护的项目对象。
- GitHub Copilot 文档建议在仓库中放置 repo-wide instructions，包含 build/test/style 等约定；本 skill 将这些拆成 `AGENT_GUIDE.md`、`STYLE_GUIDE.md`、`TESTING_GUIDE.md` 和 `FILE_MAP.md`。
- Anthropic Claude Code 文档强调通过项目记忆、工作流和 skills 传递上下文；本 skill 使用 `.vibe-spec/` 做跨工具项目记忆。
- 多篇 vibe coding 经验文章强调 context、planning、review、error handling、test coverage、security 和 repeatable workflows；本 skill 将这些转成生命周期门禁、review checklist、drift audit 和实验/测试记录。

参考链接：

- https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html
- https://docs.github.com/copilot/how-tos/agents/copilot-coding-agent/best-practices-for-using-copilot-to-work-on-tasks
- https://docs.github.com/en/copilot/get-started/best-practices
- https://docs.anthropic.com/en/docs/claude-code/overview
- https://docs.anthropic.com/en/docs/claude-code/memory
- https://docs.anthropic.com/en/docs/claude-code/common-workflows
- https://docs.anthropic.com/en/docs/claude-code/skills
- https://www.producttalk.org/vibe-coding-best-practices/
- https://roadmap.sh/vibe-coding/best-practices
