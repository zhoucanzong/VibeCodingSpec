---
message_id: unknown
kind: update
sender: unknown
recipient: unknown
reply_to: none
task_id: none
revision: unknown
rules_revision: unknown
endpoint: unknown
verdict: none
---
# 消息或真实回执

写自含主题、来源、授权范围、目标、必要上下文和回邮地址。
回执保存实际接收内容及来源证据，不得预填代表对方的确认。
hello_ack 的 revision 是已确认规范版本，endpoint 是当前会话地址；acceptance 的 revision 是交付版本。
acceptance 的 rules_revision 与任务采用的规范版本一致。
