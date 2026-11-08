# p1/docs 索引

轻量分区说明（2026-11-08）。**根目录文件路径被预注册 / run_meta / 冻结核验脚本硬编码，禁止移动。**

## 根目录（冻结路径，保持原位）

| 文件 | 用途 |
| --- | --- |
| `v1.2_experiment_preregistration.md` | P1 协议（run_meta `protocol` 字段） |
| `v12f_validation_preregistration.md` | V12-F 确认性预注册 |
| `v12f_validation_preregistration_addendum_*.md` | 双 Token / P3-A 等补记 |
| `v12f_independent_validation_preregistration.md` | 独立任务集预注册 |
| `vso_fault_injection_evaluation_design.md` | VSO 故障注入冻结设计 |
| `independent_taskset_design.md` | 独立任务集设计 |
| `part6_literature_verified.md` | 文献核验 |

## 按版本子目录（可移动的设计/历史文档）

| 目录 | 内容 |
| --- | --- |
| `v0.2/` | P1 v0.2 协议与 schema |
| `v1.0/` | P1 v1.0 任务集设计、评审、变更记录 |
| `v1.1/` | V1.1 架构/协议/失败分析与 V1.1.1 审计 |
| `v1.2/` | V1.2 架构、方法形式化、路线图等（**预注册仍在根目录**） |

## 约定

- 新增**非冻结**设计文档 → 按版本放入子目录。
- 新增**预注册 / 冻结补记** → 放根目录，并同步更新引用它的 `run_meta` / freeze JSON。
- 实验产物与报告在 `p1/experiments/`、`p1/results/`，不按本索引移动。
