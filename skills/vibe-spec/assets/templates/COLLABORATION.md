---
coordinator: unknown
rules_revision: unknown
---
# 团队与主管运行手册

用户指定主管后，填写 coordinator 为 agents/ 中的稳定成员 ID。rules_revision 使用批准的规范版本或不可变提交引用；不是“latest”。成员更换工具只更新 endpoint 与握手，职责 ID 保留。

## Mandate

记录用户目标、直接授权来源、可联系成员、允许的委派/回报范围、预算或并行限制、完成条件。未给出的权限不自行扩大。日常任务拆分、协调、催办、复核在既有授权内由主管处理。

## Responsibilities

- coordinator（P8 类比）：全局 HANDOFF/ROADMAP、规范版本、依赖协调、集成验收和对用户汇总。
- lead（P7 类比）：长期主线及 Spec、任务拆分、专项委派、进度与成果验收。
- worker（P6 类比）：限定任务的实现或调查；reviewer：独立审查。小团队允许主管兼任主线负责人，不能自称独立审核者。
- 每个成员单独维护 agents/<agent_id>.md 的进展；主管整合，全员避免并发写同一全局文件。新会话先读本页、自己的记录和分配的任务，再按项目读取顺序补齐上下文。

## Connection

1. 用户给出 terminal/会话/目录线索后，主管用当前宿主能力定位唯一目标。目录有多个会话时须进一步定位；terminal 标签不是通用地址。
2. agents/ 中登记 role、transport、endpoint、workspace、status=invited。主管本身使用 transport=self、status=local。
3. 主管以唯一消息 ID 发起握手；收到目标的真实回复后，把回复存为 messages/<id>.md，kind=hello_ack、sender=成员 ID、recipient=主管 ID、reply_to=原握手 ID、revision=已确认规范版本、endpoint=当前会话地址。
4. 成员的 hello_message 填原握手 ID，hello_ack 填回复文件的 workspace 相对路径（如 collaboration/messages/ack-a.md）。确认回复中的目录、身份、规则版本与目标一致后标 connected。工具发送成功只代表投递，不代表握手完成。
5. 更换 endpoint/session、规则版本或发现成员失联，重做握手/同步确认；旧回执不能证明新会话已连接。只对已连接成员委派执行，其他主线可继续。

## Delegation

任务使用 tasks/<task_id>.md，每个任务恰好一个 owner 与一个 acceptor。填写 spec_id（实际 Spec ID）、stream（稳定主线名）、depends_on、base_revision、rules_revision、workspace、write_scope（仓库相对的文件/目录，无 glob；只读任务用 []）、目标、验收标准和资源预算。跨仓库分别建治理工作区，接口通过任务链接协调。

depends_on 只引用当前治理工作区的任务 ID。跨仓库交付时，在消费方创建“外部交付接入”任务：Result 链接来源仓库、来源任务和不可变交付版本；由消费方负责人验证接口/产物并由其 acceptor 验收。本地主线依赖这个已验收接入任务，不能直接把远端任务 ID 填入 depends_on 或只凭远端自报完成。外部负责人如需参与本地回执，先登记为可连接成员。

状态路径：draft -> assigned -> running -> submitted -> accepted；遇阻碍转 blocked，恢复后回 assigned/running；取消用 cancelled。submitted 验收不通过回 running，并记录缺陷。修改已验收交付应建新任务或重新开放，旧验收不沿用。

- assigned 前 owner 和 acceptor 均可联系，owner 确认接单后才 running；缺依赖则 blocked。
- execution_state 记录 not_started / may_be_running / stopped。只有从未派发执行、仍在等待前置条件的 blocked 任务可填 not_started，此时不占写范围；开始运行即改 may_be_running。失联或已执行后阻塞不能改回 not_started，未确认停止前继续占用；确认停止后由主管取消旧任务并按需建立后续任务。
- 尽量一个主线一个 worktree/分支；共享目录边界划小。相同路径即使在不同 worktree 也有集成冲突风险，使用 depends_on 顺序执行或主管重新分配 write_scope。
- 文件所有权是治理约定，不是操作系统锁。范围冲突任务不能同时运行。
- 任务转交必须有原进度、改动、验证、阻塞和新 owner 回执；主管、负责人或工具切换后以任务记录恢复。

## Management Loop

1. 读成员回复，更新任务进展、主线依赖、成员工作状态；目标变动通知相关成员，全局规范版本变动按第 6 步同步。
2. 对可执行且依赖已验收的任务派发；专项成员返回给负责人，负责人验收并向主管汇总。
3. 等待实际宿主的完成/消息事件，或在约定检查点读取信箱；避免高频轮询。一次等待应允许响应用户新输入。
4. 失联或超时记 blocked，确认原执行已停止后再重派，避免重复写。未确认停止的任务保留写范围占用，或由主管明确隔离旧产物后取消。
5. 用户直接与负责人改目标时，负责人记录原始指令来源、变更和影响，通知主管；主管更新计划并同步受影响成员，无需重复审批已明确的指令。
6. TEAM 的 rules_revision 表示全局规范基线。变更后通知所有连接成员，并重新收取带新版本的确认回执；仅受影响任务暂停实现并核对差异，必要时 Spec 进入 needs_sync。无影响主线回复“已核对、无影响”后更新成员及未完成任务的版本；未确认前检查会提示 drift。只影响单个任务的细节放入该任务/Spec，不无故提升全局版本。
7. 主管汇总整体进展、已验收成果、关键阻塞及下一动作。只有方向冲突、超出授权或无法消解的依赖才交给用户决定。
8. 当本轮目标完成，停止继续派生任务，完成集成与独立审查。跨轮次继续先重读记录；后台持续运行须由实际宿主调度能力支持，不能承诺文件信箱会自动唤醒成员。

## Acceptance

submitted 必须填写 deliverable_revision、Verification 和 Result：具体提交/diff、变更文件、实际命令结果、未解决风险。acceptor 对照验收条件检查交付；独立 Reviewer 的审查不能由实现者代签。

accepted 必须记录 kind=acceptance 的真实验收回执，sender=acceptor、recipient=owner、task_id=当前任务、revision=deliverable_revision、rules_revision=任务规范版本、verdict=pass；acceptance 字段指向该文件。Verification 写实际 `- Result: \`command\` -> PASS (exit 0)`；只读调查可记录实际检查命令及结果。所有依赖先 accepted。acceptor 与 owner 必须不同。

任务 accepted 只代表该次委派验收；Spec 仍按原生命周期经过验证和 Post-Build Review，主管完成集成测试后才汇总为全局完成。修改任务采用的规范/交付版本后旧验收失效；历史已验收任务保留原版本，新的影响另建后续任务。

## Storage

agents/ 存成员及其主线交接，tasks/ 存委派与状态，messages/ 存必要握手、决定和验收回执。templates/ 仅为模板，不是已连接成员或真实任务。

运行时地址如有隐私需要，使用用户可访问的本地忽略文件；持久记录只保存对应引用。秘密令牌不能入库。只保存关键消息，不复制全部聊天日志。共享信箱必须约定唯一实际路径，worktree 私有副本由主管归并关键事实。
