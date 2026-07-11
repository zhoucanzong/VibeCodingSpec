# vibe-spec 生产级自动化设计

## 背景

`vibe-spec` 已具备中文规格模板、profile/module 初始化、生命周期说明、跨 Agent 接手协议和基础健康检查。当前主要缺口是：创建 spec、状态推进、审核、状态汇总和 CI 接入仍依赖 Agent 手工维护，容易造成索引、日志和实际状态不一致。

本轮目标是在保留 Skill 特点的前提下补齐生产级治理闭环。`vibe-spec` 仍由 Agent 理解上下文、询问用户、判断质量并协调审查；脚本只自动化确定性、重复且容易出错的机械操作。

## 设计原则

1. **Agent-first**：`SKILL.md` 是工作流入口和决策中心，CLI 不是独立产品。
2. **仓库即事实来源**：长期状态保存在 Markdown 中，不引入数据库或第二套状态文件。
3. **渐进式披露**：核心流程保留在 `SKILL.md`，详细规则放入 references，模板和脚本按需使用。
4. **可降级执行**：没有脚本或 subagent 时，Agent 仍可按文档完成同一流程。
5. **确定性自动化**：文件生成、状态合法性、索引同步和结构检查交给零依赖脚本。
6. **能力按需启用**：CI、hooks、跨 Agent 入口和机器输出在 init 时选择，不强制全量安装。

## 架构

采用“Skill 编排层 + 共享脚本核心 + 独立命令 + 模板/reference”的结构：

```text
skills/vibe-spec/
  SKILL.md
  agents/openai.yaml
  references/
    automation.md
    lifecycle-governance.md
    review-checklist.md
    ...
  assets/templates/
    FEATURE_SPEC.md
    REVIEW_REPORT.md
    AGENT_ENTRY.md
    github-actions-vibe-spec.yml
    ...
  scripts/
    vibe_spec_core.py
    init_vibe_spec.py
    create_spec.py
    promote_spec.py
    create_review.py
    status_vibe_spec.py
    prepare_review_context.py
    check_vibe_spec.py
    install_git_hooks.py
  tests/
```

共享核心只负责 Markdown frontmatter、章节、生命周期日志、spec 查找、索引重建和 JSON 输出。每个命令保持单一职责，可由 Agent 直接运行，也可根据 reference 手工完成等价操作。

## Skill 工作流

### Init

Agent 先检查仓库，再询问或推断：

- profile：`minimal`、`standard`、`production`
- 额外治理模块
- 是否生成 `CLAUDE.md`、`AGENTS.md` 等薄入口
- 是否安装 GitHub Actions 模板
- 是否安装本地 Git hooks

非交互环境通过脚本参数显式选择。已有文件不覆盖；薄入口只指向 `.vibe-spec/AGENT_GUIDE.md`，不复制规则正文。

### Spec 创建

Agent 负责澄清需求和填写高质量内容。`create_spec.py` 负责生成合法文件名、唯一 `spec_id`、frontmatter、日期、模板和 `SPEC_INDEX.md` 条目。空模板不能直接推进到 `approved`。

### 生命周期推进

`promote_spec.py` 实现允许的状态图，并检查确定性门禁：必需章节、占位符、实现记录、验证证据、审核记录和替代关系。Agent 额外判断内容质量和证据可信度。每次推进原子更新 spec frontmatter、`Lifecycle Log` 和 `SPEC_INDEX.md`。

状态回退、`sync`、`retire` 复用同一推进机制，并要求提供原因。非法跳转返回非零，不修改文件。

### Post-build Review

完成实现后，Skill 默认进入 review 路径：

- 当前工具支持 subagent 时，由 Agent 启动独立审查者。
- 不支持时，按统一 checklist 自审并明确标记审查方式。
- `prepare_review_context.py` 只收集 spec、diff 摘要、验证命令和相关文件清单，避免泄露实现者结论。
- `create_review.py` 生成结构化报告并将结论关联回 spec。

脚本不伪装成独立审查者，也不以结构检查替代工程判断。

### Status 与 Audit

`status_vibe_spec.py` 从 spec 文件重建状态视图，展示状态分布、阻塞项、待同步项和建议下一步。`check_vibe_spec.py` 扩展索引一致性、继承引用、重复 ID、生命周期证据和模块配置检查。

人类输出使用 Markdown/文本；所有主要脚本支持 `--json`，JSON 仅作为即时输出。

## CI 与 Hooks

GitHub Actions 模板执行：

1. Python 单元测试
2. `check_vibe_spec.py --strict`
3. 可选 spec drift 检查

hooks 为显式安装项：`pre-commit` 执行快速结构检查，`pre-push` 执行严格检查。安装器必须备份或拒绝覆盖已有 hook；默认不修改 `.git/hooks`。CI 模板和 hooks 都可不启用，不影响 Skill 核心能力。

## 数据与错误处理

- Markdown frontmatter 使用受控的简单标量和列表语法，标准库解析，不引入 YAML 依赖。
- 修改前完成所有校验；多文件更新使用临时文件和替换，尽量避免半更新状态。
- 命令错误输出包含错误码、文件位置和建议动作。
- `--json` 保持稳定字段：`ok`、`command`、`changes`、`findings`、`next_actions`。
- 已存在的用户内容优先保留；无法安全合并时停止并交给 Agent 判断。

## 测试策略

使用标准库 `unittest` 和临时目录覆盖：

- 各 profile/module 初始化与幂等性
- 跨 Agent 薄入口和 CI 可选生成
- spec 创建、重复 ID 和命名规范
- 合法与非法状态流转
- 各生命周期门禁失败和成功
- spec、生命周期日志、索引三者同步
- review 报告与审查上下文生成
- status 文本和 JSON 输出
- check 对继承、索引和模块漂移的检查
- hooks 不覆盖已有用户 hook

目标运行环境为 Python 3.10+，不依赖第三方包。

## 交付边界

本轮不会构建常驻服务、数据库、Web UI、完整 Python 包或厂商专属 Agent SDK。不会让脚本直接调用 Claude/Codex API。厂商能力差异由 Skill 的能力检测和降级路径处理。

完成标准：Claude 风格命令和 Codex 自然语言调用都有明确路径；核心生命周期可以自动校验和同步；生产增强项可选启用；测试、严格检查和独立审查通过。
