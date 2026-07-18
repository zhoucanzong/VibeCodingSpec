# Vibe Spec

面向 Claude、Codex、Cursor 等 coding agent 的跨工具规格驱动开发 Skill。

`vibe-spec` 把代码层级、项目规范、当前工作、未来计划、spec 生命周期、实现记录、测试证据和审核结论沉淀在仓库中。切换工具后，新 Agent 从同一个交接入口继续工作，不依赖上一工具的隐藏记忆。

## 设计定位

`vibe-spec` 是 Agent-first Skill，不是独立 CLI 产品：

- `SKILL.md` 负责理解请求、读取上下文、判断质量并协调 review。
- Markdown 是项目长期事实来源。
- Python 脚本只自动化创建、状态门禁、索引同步和结构检查。
- 没有脚本或 subagent 时，Agent 仍可按 references 完成等价流程。
- CI、Git hooks、Claude/Codex/Cursor 入口均为可选能力。

## 核心能力

- 按 `minimal`、`standard`、`production` profile 初始化 `.vibe-spec/`。
- 按模块启用 testing、data、experiments、security、release、migration、observability 等治理能力。
- 使用 `HANDOFF.md` 记录正在进行的工作、阻塞、验证和下一动作。
- 使用 `FILE_MAP.md` 描述代码层级、入口、目录职责和依赖方向。
- 使用 `ROADMAP.md` 维护 now、next、later、done。
- 创建、继承、同步、替代和退役 spec。
- 通过状态机与内容门禁维护完整生命周期。
- 实现后自动进入 subagent 优先的 Post-Build Review。
- 生成不包含实现者结论的独立审查上下文。
- 检查索引漂移、重复 ID、断裂引用、缺失证据和交接缺口。
- 支持稳定 `--json` 输出、GitHub Actions 和显式 Git hooks。

## 安装

让 coding agent 从仓库安装该 Skill：

```text
安装这个 skill：git@github.com:zhoucanzong/VibeCodingSpec.git
```

Skill 入口为 `skills/vibe-spec/SKILL.md`。

## 使用

Claude 风格命令：

```text
/vibe-spec init production
/vibe-spec context
/vibe-spec handoff
/vibe-spec roadmap
/vibe-spec spec Add passwordless login
/vibe-spec build passwordless-login
/vibe-spec promote passwordless-login verified
/vibe-spec review passwordless-login
/vibe-spec status
/vibe-spec check --strict
/vibe-spec sync passwordless-login
/vibe-spec retire passwordless-login
```

Codex 或其他 Agent 可以自然语言调用：

```text
使用 vibe-spec 接手这个项目，告诉我正在进行的工作和下一步。
使用 vibe-spec 为 passwordless login 创建并维护一个 spec。
使用 vibe-spec 按已批准的 spec 实现，完成后进行独立审核。
```

## 目标项目结构

```text
.vibe-spec/
  HANDOFF.md           # 固定接手入口：当前目标、工作、阻塞、验证、下一动作
  AGENT_GUIDE.md       # 跨 Agent 行为规则与读取顺序
  PROJECT_SPEC.md      # 项目目标、用户、范围和边界
  FILE_MAP.md          # 代码层级、目录和关键文件职责
  STYLE_GUIDE.md       # 工程、UI、命名和架构规范
  DECISIONS.md         # 长期产品与技术决策
  SPEC_INDEX.md        # 所有 spec 的状态、依赖和下一步
  ROADMAP.md           # now / next / later / done
  LIFECYCLE.md         # 状态机、门禁和维护规则
  MODULES.md           # 已启用治理模块
  specs/               # 功能 spec
  reports/             # review、audit 和 review context
  scripts/             # 可选项目本地治理脚本
  *_GUIDE.md           # 按模块启用的 testing/data/production 规范
```

可选生成的 `CLAUDE.md`、`AGENTS.md` 和 Cursor rule 都是薄入口，只指向 `.vibe-spec/HANDOFF.md` 与 `AGENT_GUIDE.md`，不会复制并分叉规则。

## 自动化脚本

```bash
# 初始化并生成 Claude/Codex 入口与 GitHub Actions
skills/vibe-spec/scripts/init_vibe_spec.py /path/to/project \
  --profile production --agent-entry claude codex --ci

# 生成代码地图候选，不修改 FILE_MAP.md
skills/vibe-spec/scripts/refresh_context.py /path/to/project --json

# 创建和推进 spec
skills/vibe-spec/scripts/create_spec.py /path/to/project login-flow --title "Login Flow"
skills/vibe-spec/scripts/promote_spec.py /path/to/project login-flow ready_for_review \
  --reason "规格已完整" --evidence "验收标准已检查"

# 维护交接、汇总状态和检查健康度
skills/vibe-spec/scripts/update_handoff.py /path/to/project \
  --goal "完成登录流程" --state in_progress --active-spec login-flow \
  --next-action "执行验证"
skills/vibe-spec/scripts/status_vibe_spec.py /path/to/project --json
skills/vibe-spec/scripts/check_vibe_spec.py /path/to/project --strict --json

# 准备和记录 review
skills/vibe-spec/scripts/prepare_review_context.py /path/to/project login-flow
skills/vibe-spec/scripts/create_review.py /path/to/project login-flow \
  --verdict pass --mode subagent --summary "验收标准全部满足"

# 显式安装 pre-commit/pre-push hooks
skills/vibe-spec/scripts/install_git_hooks.py /path/to/project
```

所有主要命令的 JSON 输出固定包含 `ok`、`command`、`changes`、`findings` 和 `next_actions`。

## 开发验证

```bash
python3 -m unittest discover -s skills/vibe-spec/tests -v
python3 -m compileall -q skills/vibe-spec/scripts
```

完整自动化参数和无脚本降级方式见 `skills/vibe-spec/references/automation.md`。
