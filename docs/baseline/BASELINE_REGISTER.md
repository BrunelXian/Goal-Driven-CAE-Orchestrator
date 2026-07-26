# AegisCAE Runtime Baseline Register

```text
document: BASELINE_REGISTER.md
project: AegisCAE Runtime
status: FROZEN_BASELINE_REGISTER
snapshot date: 2026-07-26
baseline count: 4
runtime input: NO
```

## Authoritative order

1. `LEGACY_MIGRATION_DECISIONS.md`
   最终迁移和架构裁决权威。

2. `AegisCAE Runtime 项目计划书.md`
   项目定位、总体架构和核心原则。

3. `LEGACY_ABQJOBPILOT_SUMMARY.md`
   AbqJobPilot 历史实现证据。

4. `LEGACY_ABQPILOT_SUMMARY.md`
   AbqPilot 历史实现证据。

两份 legacy summary 是历史事实和迁移参考，不是新 Runtime contract。

四份 baseline 文件是 documentation snapshots，不是 Runtime 配置文件，也不得在
生产代码中读取。

发生冲突时，以 `LEGACY_MIGRATION_DECISIONS.md` 为准。

## Relocation provenance

The temporary source hashes were recorded before canonical relocation.
The final canonical files retain the same previously validated SHA-256 values.
The baseline contents were not edited during relocation.

```text
temporary source removed after verified canonical relocation: YES
```

## Registered snapshots

| ID | Canonical filename | Document role | Precedence | Source path | Destination path | SHA-256 | Snapshot date | Content changed | Runtime input |
|---|---|---|---:|---|---|---|---|---|---|
| BL-001 | `LEGACY_MIGRATION_DECISIONS.md` | Final migration and architecture decision authority | 1 | `docs/baseline/00_LEGACY_MIGRATION_DECISIONS.md` | `docs/baseline/LEGACY_MIGRATION_DECISIONS.md` | `d90e35737ee86a3aa77b67afa5d6becf4977a371f35517317615db351e3603c2` | 2026-07-26 | NO | NO |
| BL-002 | `AegisCAE Runtime 项目计划书.md` | Project positioning, architecture, and core principles | 2 | `docs/baseline/00_AegisCAE Runtime 项目计划书.md` | `docs/baseline/AegisCAE Runtime 项目计划书.md` | `9a89a5ad661a80a69ec159124066e5b34ed6dc74de9295336f426b17079e7448` | 2026-07-26 | NO | NO |
| BL-003 | `LEGACY_ABQJOBPILOT_SUMMARY.md` | AbqJobPilot historical implementation evidence | 3 | `docs/baseline/00_LEGACY_ABQJOBPILOT_SUMMARY.md` | `docs/baseline/LEGACY_ABQJOBPILOT_SUMMARY.md` | `f938b243ff438c6e7587f9337be4c4730e4bddeed78a874a5bd4e0f2a1128dfb` | 2026-07-26 | NO | NO |
| BL-004 | `LEGACY_ABQPILOT_SUMMARY.md` | AbqPilot historical implementation evidence | 4 | `docs/baseline/00_LEGACY_ABQPILOT_SUMMARY.md` | `docs/baseline/LEGACY_ABQPILOT_SUMMARY.md` | `d1685d26a208f15ad772335fcd927c0c22f31f0fe8901613d9a7b02ac9591a43` | 2026-07-26 | NO | NO |

## Change policy

1. 不允许静默覆盖 baseline。
2. 不允许直接修改已登记 snapshot。
3. 新裁决必须通过 ADR 或新的 superseding decision document。
4. 更新 baseline 时必须重新计算 SHA-256。
5. 任何 hash 变化必须进入独立 reviewed commit。
