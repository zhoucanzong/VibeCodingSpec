# Vibe Spec

面向 Claude、Codex、Cursor 等 coding agent 的跨工具规格驱动开发工作流。

`vibe-spec` 把项目意图、spec 继承、生命周期、实现记录、实验数据、测试验证和审核结果沉淀到仓库里，让不同 Agent 可以按同一套规则接手和维护项目。

## 它解决什么

- 按 `minimal`、`standard`、`production` profile 初始化项目级 `.vibe-spec/` 工作区。
- 按模块启用治理能力，避免一开始生成不需要的文件。
- 将需求转成可实现、可审核、可继承的 spec。
- 维护 spec 生命周期：`draft`、`approved`、`implemented`、`verified`、`reviewed`、`active`、`deprecated` 等。
- 支持 spec 继承、override、supersession、sync 和 retire。
- 指导 Agent 按 spec 实现，而不是靠隐式记忆。
- 审核实现是否满足 acceptance criteria。
- 审计 spec/code drift。
- 维护文件地图，让 Agent 知道重要文件和目录是什么。
- 规范实验记录、数据位置、fixtures、测试命令和验证脚本。

## 安装

让你的 coding agent 安装这个 skill：

```text
安装这个 skill：git@github.com:zhoucanzong/VibeCodingSpec.git
```

Skill 入口：

```text
skills/vibe-spec/SKILL.md
```

## 用法

Claude 风格 slash command：

```text
/vibe-spec init
/vibe-spec init minimal
/vibe-spec init standard
/vibe-spec init production
/vibe-spec init standard --modules data experiments
/vibe-spec enable security
/vibe-spec spec Add passwordless login
/vibe-spec build passwordless-login
/vibe-spec review passwordless-login
/vibe-spec update passwordless-login
/vibe-spec lifecycle passwordless-login
/vibe-spec promote passwordless-login verified
/vibe-spec sync passwordless-login
/vibe-spec retire passwordless-login
/vibe-spec experiment login-benchmark
/vibe-spec audit
/vibe-spec status
```

Codex 或其他 Agent 的自然语言调用：

```text
使用 vibe-spec 初始化这个仓库。
使用 vibe-spec 为 passwordless login 写一个 spec。
使用 vibe-spec 实现已批准的 passwordless-login spec。
使用 vibe-spec 检查这个项目有没有 spec drift。
```

## 项目工作区

在目标项目里初始化后，`vibe-spec` 根据 profile/module 生成：

```text
.vibe-spec/
  PROJECT_SPEC.md
  AGENT_GUIDE.md
  STYLE_GUIDE.md
  DECISIONS.md
  LIFECYCLE.md
  MODULES.md
  FILE_MAP.md
  DATA_GUIDE.md
  TESTING_GUIDE.md
  EXPERIMENTS.md
  SECURITY_GUIDE.md
  RELEASE_GUIDE.md
  MIGRATION_GUIDE.md
  ENVIRONMENT_GUIDE.md
  OBSERVABILITY_GUIDE.md
  CONTRACTS.md
  SPEC_INDEX.md
  specs/
  reports/
  scripts/
```

这些文件是 Agent 之间的交接层。Claude、Codex、Cursor 和后续工具都应先读它们，再改代码。

## Init Profiles

`init` 支持三种档位：

| Profile | 默认模块 | 适合场景 |
|---|---|---|
| `minimal` | `core` | 原型、小项目、刚开始探索 |
| `standard` | `core,memory,testing,review` | 常规应用开发 |
| `production` | `core,memory,testing,review,data,experiments,security,release,migration,environment,observability,contracts,scripts` | 生产项目 |

脚本用法：

```bash
skills/vibe-spec/scripts/init_vibe_spec.py /path/to/project --profile minimal
skills/vibe-spec/scripts/init_vibe_spec.py /path/to/project --profile standard
skills/vibe-spec/scripts/init_vibe_spec.py /path/to/project --profile production
skills/vibe-spec/scripts/init_vibe_spec.py /path/to/project --profile standard --modules data experiments
```

如果一开始不确定，先用 `minimal` 或 `standard`，之后再启用模块：

```bash
skills/vibe-spec/scripts/init_vibe_spec.py /path/to/project --profile minimal --modules security release
```

## Skill 结构

```text
skills/
  vibe-spec/
    SKILL.md
    assets/
      templates/
        AGENT_GUIDE.md
        AUDIT_REPORT.md
        DATA_GUIDE.md
        DECISIONS.md
        EXPERIMENTS.md
        FEATURE_SPEC.md
        FILE_MAP.md
        LIFECYCLE.md
        MODULES.md
        SECURITY_GUIDE.md
        RELEASE_GUIDE.md
        MIGRATION_GUIDE.md
        ENVIRONMENT_GUIDE.md
        OBSERVABILITY_GUIDE.md
        CONTRACTS.md
        PROJECT_SPEC.md
        REVIEW_REPORT.md
        SPEC_INDEX.md
        STYLE_GUIDE.md
        TESTING_GUIDE.md
    references/
      agent-compatibility.md
      lifecycle.md
      lifecycle-governance.md
      review-checklist.md
      spec-drift.md
      vibe-coding-field-notes.md
    scripts/
      init_vibe_spec.py
```

## 核心思想

Spec 不应该是一次性计划，而应该是项目长期资产：

- Spec 可以继承项目级规则或父 spec。
- Spec 可以新增行为，也可以显式 override 继承行为。
- 生命周期日志记录状态如何变化、为什么变化、证据是什么。
- 实现记录说明改了什么和为什么。
- Review 记录验收标准是否真的满足。
- Audit 捕捉代码和 spec 的漂移。
- Experiments 记录输入、命令、指标、产物和决策影响。
- Data 和 Testing guide 让验证可以被不同工具复现。
