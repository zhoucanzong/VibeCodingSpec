---
experiment_id: unknown
run_id: unknown
owner: unknown
status: planned
created: unknown
started: unknown
ended: unknown
plan_snapshot: unknown
plan_sha256: unknown
code_revision: unknown
patch: none
data_version: unknown
model: unknown
seed: unknown
exit_code: unknown
artifacts_status: pending
---
# 单次运行

## Configuration

unknown

## Environment

unknown

## Command

unknown

## Metrics

unknown

## Observations

unknown

## Artifacts

| Path | SHA256 | Purpose |
|---|---|---|

## Limitations

unknown

## Progress

开始执行前填实际代码、数据、模型、参数、种子、依赖和命令；执行后填 UTC 时间、退出码、观测和产物。无适用模型或随机种子时填 not_applicable，并在 Configuration 解释。中断无法取得退出码时填 unknown，说明原因；不得预填成功。
未启动就取消时使用 cancelled，started/exit_code 保留 unknown，记录实际取消时间 ended 与原因 Observations；不编造一次执行。
