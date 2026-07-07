# 数据指南

用于让数据存放、隐私规则、fixtures 和实验输入可复现。

## 数据位置

| 路径 | 类型 | 来源 | 使用方 | 是否提交 | 备注 |
|---|---|---|---|---|---|
| TBD | raw / derived / fixture / export | TBD | TBD | yes/no | TBD |

## 数据规则

- raw data 与 derived data 分开存放。
- 不提交 secrets、credentials、私有用户数据或大型生成产物，除非用户明确批准。
- derived datasets 要记录来源、生成命令、时间戳和 schema。
- 测试优先使用小型、确定性的 fixtures。
- 记录生成数据的清理和保留规则。

## Schema

| 数据集/文件 | 字段 | 校验方式 | 备注 |
|---|---|---|---|
| TBD | TBD | TBD | TBD |

## 隐私与敏感性

- 敏感数据类型：TBD
- 脱敏/匿名化规则：TBD
- 存储限制：TBD

## 可复现性

任何用于实验或测试的数据集都要记录：

- 来源路径或 URL。
- 版本、hash 或时间戳。
- 转换脚本或命令。
- 预期输出位置。
