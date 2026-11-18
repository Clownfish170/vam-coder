# experiments/V13E — 旗舰主实验

56 repository-editing 合成任务 + 双模型主实验；**主定位**，P1-TRANSFER 不得取代。

## 本目录（衍生材料已迁入）

| 子目录 | 内容 |
| --- | --- |
| `robustness/` | `V13E_CLUSTER_ROBUSTNESS_AUDIT.md` |
| `reports/` | `V13E_v0.5_readonly_evidence_audit.md` |
| `protocol/` `configurations/` `tasks/` `runs/` `raw/` `processed/` `statistics/` `fault-injection/` | 占位；见 canonical |

## canonical 物理路径（未移动）

| 类型 | 路径 |
| --- | --- |
| 主 run | `p1/experiments/v13e_sah/runs/`, `p1/experiments/v13e_crossmodel/runs/` |
| 预注册 | `p1/docs/v13e_crossmodel_preregistration_draft.md`（freeze JSON 引用） |
| 设计 | `p1/docs/v13e_sah_design.md`（run_meta `design` 字段） |
| VSO 注入 | `p1/experiments/vso_fault_injection/` |
| 双 Token（探索，非主实验） | `p1/experiments/dualtoken_ablation/` → 见 `development/V1.3/exploration/` |

架构臂：F / PROJ(S1) / SAH(S1+S2) / MOFF — 见 `p1/scripts/v12/config.py`
