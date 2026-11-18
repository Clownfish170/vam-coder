# experiments/ — 独立实验体系（组织层）

**重要：** 冻结 run 数据的 **canonical 物理路径** 仍在 `p1/experiments/**`（脚本与 `run_meta`/`code_snapshot` 硬编码）。  
本树按职责存放**已迁入的衍生材料**与**指针 README**；**不**搬迁 `runs/` 原始数据。

| 目录 | 覆盖 | canonical 物理路径 |
| --- | --- | --- |
| [V12-F/](V12-F/README.md) | V12-F 确认性/消融 | `p1/experiments/p1_validation` `p2_ablation` `p3_crossmodel_qwen` `validation_p0` `v12_p*` 等 |
| [V13E/](V13E/README.md) | 旗舰主实验 | `p1/experiments/v13e_sah` `v13e_crossmodel` `vso_fault_injection` 等 |
| [P1-TRANSFER/](P1-TRANSFER/README.md) | 真外部扩展 | `p1/experiments/v13e_p1_transfer` `v13e_p1_swebench` |

任务集 canonical：`p1/tasks*/` · manifest：`p1/manifests/`  
完整索引：`docs/EXPERIMENT_INDEX.md`
