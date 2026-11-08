# V1.3 最小验证实验设计（只设计，不执行）

## 目标

验证：**adaptive_a（默认 Digest + 高信息升 Full）** 相对 E/F 的 ESR/TPAE 折中，且安全不变式保持。

## 臂

| 臂 | 策略 |
| --- | --- |
| E | 恒 Digest（基线） |
| F | 恒 Full（基线） |
| **V1.3-A** | adaptive_a（待实现） |

（可选 V1.3-C 成本约束，第二轮再议。）

## 任务与重复

| 项 | 建议 |
| --- | --- |
| 任务 | **24 全集**（禁止只选 CFD03）；若资源紧则 **分层抽样** ≥12：含全部 cross_file_dep + 随机非 cross ≥6 |
| R | **2**（最小）或 **3**（与 P1 对齐） |
| 请求上界 | 12×3arms×R2×2steps=144；24×3×3×2=432 |

**独立验证**：规则在本集探索则标 exploratory；正式主张需 **第二任务集**（新 tasks 快照）或冻结规则后新项目。

## 随机化

独立 `randomization_manifest`，seed 与主实验区分（如 20261103），记录于 run_meta。

## 指标

ESR、SPR、TPAE、TPSE、FETC、Wilson CI、task-cluster bootstrap（B=10000, seed 冻结）。  
安全：ET/C FULL、VP pre_send、INSUFFICIENT、DHO=0。

## 成功判据（预注册草案）

1. **安全**：V1.3-A 与 E 相同，DHO=0，无 ET 违规。  
2. **效率**：TPAE(V1.3) ≤ TPAE(F) − 1%（保守）或 ≤ TPAE(E)+2%。  
3. **准确率**：ESR(V1.3) ≥ ESR(E) − 0.05；且 ESR(V1.3) ≥ ESR(F) − 0.05。  
4. **机制**：CFD03 类任务 V1.3 应升 Full 且 ESR 不低于 F。  

阈值在开跑前冻结；禁止事后改。

## 资源

- 144–432 请求；串行 1–2h 量级（8192 ctx）  
- 独立输出目录 `v13_validation_*`，不覆盖 P1  

## 禁止

- 只跑 F 占优任务  
- 用 P1 结果直接当 V1.3 独立验证  
- 改 VP/ET/must  
