# P3-A 跨模型泛化报告：`vam_coder_v1.2_F` 在 qwen3.8-flash 上的独立验证

状态：**完成**（预注册 v1 §9 + 补记 P3-A）。架构完整英文标识；**按补记约定与 deepseek 轮分模型独立报告，不合并原始成功率**。  
补记：`p1/docs/v12f_validation_preregistration_addendum_p3a.md`（sha `2ce8de…`，声明于任何 P3-A 请求之前）。

---

## 1. 环境与执行

| 项 | 值 |
| --- | --- |
| 模型 | **`qwen3.8-flash`**（用户选定；与主实验 deepseek-v4.1-flash-1017 不同厂商家族） |
| 参数 | 与 P1 冻结一致：max_tokens=2048、temp0、seed0、history=keep、48 题、三臂、R=5 |
| 随机化 | seed=20261109（仅顺序）；bootstrap 20261102、cluster=task_id（**R5 不视为 720 个独立样本**） |
| 规模 | **720/720 episodes OK**、4080 步请求、**3,662,576 tokens（S5=6M 的 61%）** |
| 中断与恢复 | 一次断电（进度 674 落盘无损）+ 一集 `RemoteDisconnected`（`p1_L07a_symbol_full_read_R2`，steps=0 零数据）→ **RC_1 记录保留 + 断点补跑完成**（infrastructure 类，非模型失败） |

## 2. 主结果（n=240 episodes/架构）

| 指标 | `vam_coder_v1.2_F` | `memory_off` | `symbol_full_read` |
| --- | ---: | ---: | ---: |
| ESR [Wilson 95% CI] | 0.8708 [0.823, 0.908] | 0.8875 [0.841, 0.922] | 0.8875 [0.841, 0.922] |
| SPR | 0.9765 | 0.9787 | 0.9801 |
| **prompt mean（median）** | **2,788（1,975）** | 3,614（2,457） | 3,643（2,483） |
| TPAE · TPSE | **4,481 · 5,146** | 5,371 · 6,052 | 5,409 · 6,094 |
| 失败集（机制） | 31（wrong 28 / proto 2 / noop 1 / infra 1） | 27（wrong 27 / noop 2） | 27（wrong 26 / infra 1 / proto 0） |

## 3. 统计（同 P1 口径：task-cluster bootstrap + sign-flip + Holm 主比较）

### RQ1 效率 —— 跨模型复现

| 主比较 | Δprompt/集 [95% CI] | ΔTPAE [95% CI] | sign-flip Holm p |
| --- | --- | --- | --- |
| F − `memory_off` | **−825.7 [−1038.8, −618.8]**（−22.9%） | −889.8 [−1343.2, −340.2] | **0.0002** |
| F − `symbol_full_read` | **−854.6 [−1074.4, −640.1]**（−23.5%） | −927.7 [−1366.6, −422.5] | **0.0002** |

### RQ2 能力保持 —— 非劣再次 PASS

| 主比较 | ΔESR [95% CI] | 边界 −12pp | 判定 |
| --- | --- | --- | --- |
| F − `memory_off` | −1.67pp [−5.83, +2.08] | 下界 −5.8pp ≫ −12pp | **PASS** |
| F − `symbol_full_read` | −1.67pp [−5.42, +1.67] | 下界 −5.4pp ≫ −12pp | **PASS** |

sign-flip ESR 不显著（Holm 0.91）；McNemar 敏感性同向不显著。

### 族级敏感性（8 族）

prompt 差值 **8/8 同号**，family sign-flip **p=0.0079 / 0.0072**——与 deepseek 轮（8/8、p≈0.007）结构完全一致；ESR 族级不显著（预期内）。

## 4. 与 deepseek 轮的方向一致性（`direction_consistency.csv`）

| 配对 · 指标 | deepseek（P1） | qwen3.8-flash（P3-A） | 同向 |
| --- | --- | --- | --- |
| F−memory_off · prompt | −777 [−975, −584] | **−826 [−1039, −619]** | ✓ |
| F−memory_off · TPAE | −787 [−979, −602] | **−890 [−1343, −340]** | ✓ |
| F−memory_off · ESR | −0.8pp [−4.2, +2.9] | −1.7pp [−5.8, +2.1] | ✓（均 ns、均过非劣） |
| F−symbol · prompt | −801 [−1003, −603] | **−855 [−1074, −640]** | ✓ |
| F−symbol · TPAE | −845 [−1059, −640] | **−928 [−1367, −422]** | ✓ |
| F−symbol · ESR | −0.8pp [−5.4, +2.9] | −1.7pp [−5.4, +1.7] | ✓（均 ns、均过非劣） |

**6/6 指标同方向**；token 效应量级 qwen 略大（−23% vs −24% 同档），ESR 两模型均"小负且不显著 + 非劣通过"。绝对水平：qwen 整体 ESR 低约 6pp（F 87.1% vs 92.9%），prompt 基线更高（+11~13%），但**架构间相对结论不变**——这正是跨模型泛化要验证的"方向一致性"，而非原始成功率可比性（补记明令不合并）。

## 5. 图表（figures/，标注 qwen3.8-flash）

图1 ESR 总体+分层 · 图2 prompt 分布 · 图3 权衡 · 图4 Long 上下文增长 · 图5 任务级差值 · 图6 失败机制 · 图7 族敏感性——结构与 P1 报告同套，标题已换模型标注。

## 6. 局限

1. 单一异族模型点（qwen）——"跨模型"=2 模型方向一致，不足以建模随机效应；
2. 一集 infrastructure 中断（RC_1 保留 + 补跑）：ESR 分母按 720 计，该集补跑结果正常计入；infrastructure 机制在失败分类中单列；
3. protocol 2 步（2048 触顶型，与归因结论一致：reasoning 烧尽预算）；
4. 任务族参数化限制同 P1（族敏感性已做）；
5. 与 1.5B 能力边界轮（round1–2）仍不合并。

## 7. 结论

**P3-A 通过**：`vam_coder_v1.2_F` 的 −23~24% 上下文节省与 ±12pp 非劣能力保持，在第二个异族云端模型上**方向复现、族级稳健、统计口径与 P1 完全一致**。至此预注册 P0–P3 中的跨模型项闭环；剩余排产项为 VSO 专项（设计稿 v2 待审）与独立任务集泛化。

## 8. 交付物

同目录：`raw_results.csv`（4080 步）、`metrics_summary.csv`、`bootstrap_results.csv`、`signflip_tests.csv`、`family_sensitivity.csv`、`failure_analysis.csv`、`direction_consistency.csv`、`analysis_manifest.json`、`figures/fig1–fig7`、`run_meta.json`（含补记 sha）、`randomization_manifest.json`、`execution_log.jsonl`（含 RC_1 审计行）、`execution_summary.json`。
