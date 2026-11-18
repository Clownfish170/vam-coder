# P1-SWEBENCH 统计字段与成本/时长估算

日期：2026-11-16  
状态：镜像 + gold 10/10 就绪；**付费全量未开跑**

---

## 1. 实验规模（正式，待你确认）

| 项 | 值 |
| --- | --- |
| 任务 | **10**（SWE-bench Lite 子集） |
| 臂 | F / PROJ / MOFF |
| reps | **3** |
| 模型 | **仅 DeepSeek** `deepseek-v4.1-flash-1017` |
| Episodes | 10×3×3 = **90** |
| 评测 | 官方镜像内跑 FAIL_TO_PASS（Docker） |

对照原 V13E：单模型 1176 集 / ≈6.55M tokens / ≈26h → 本实验约为其 **~1/3 集数**。

---

## 2. 必采统计（能记的都记）

### 2.1 Episode 级（每条 90 行）

| 字段 | 含义 |
| --- | --- |
| instance_id / repo / base_commit | 任务身份 |
| arm / label / rep / model | 臂与重复 |
| prompt_sum / completion_sum / total_tokens | **API 计量**（主指标） |
| cached_tokens_sum | 缓存命中 |
| episode_success (resolved_local) | 全步骤 + FAIL_TO_PASS 通过 |
| step_eval[] | 每步 eval 0/1 |
| insufficient_sum | fail-closed 次数 |
| pre_send_revised_sum / force_full_n_sum | VSO 回退 |
| sah_folded_blocks_sum | S1 折叠（机制门） |
| n_steps / applied_files | 轮数与改动文件 |
| t_model_ms / t_eval_ms / t_step_ms / t_assemble_ms | 分段耗时 |
| errors / api_error / http_status | 异常 |
| usage_source | api \| estimate |
| config_sha256 | 臂配置指纹 |

### 2.2 Step 级（沿用 V13E result.json）

prompt/completion、peak context、pre_send、insufficient_reason、folded、apply 结果、eval_output 摘要。

### 2.3 Docker 评测级

| 字段 | 含义 |
| --- | --- |
| eval_elapsed_s | 容器评测耗时 |
| docker_rc / status | ok/fail/env_fail |
| gold_apply_failed / test_apply_failed | 补丁应用 |
| n_nodes | FAIL_TO_PASS 数 |
| resolved_local | **主 ESR 分量** |

### 2.4 汇总（分析脚本输出）

- 按臂：ESR、prompt/集、completion/集、insufficient、folded、eval 耗时  
- 配对：PROJ−F、PROJ−MOFF、F−MOFF（instance×rep）  
- 分层：按 repo（requests/pytest/flask/pylint）  
- 与原 V13E：**分表**，不合并绝对值  

---

## 3. Gold 基线（已测，非付费推理）

| 指标 | 值 |
| --- | --- |
| gold resolved | **10/10** |
| 单次容器评测均耗时 | **≈11.2 s** |
| 10 题 gold 总耗时 | ≈2 min（含启动） |

→ 正式 90 次评测 ≈ 90×11s ≈ **16–20 min**（评测侧，不含模型）。

---

## 4. 付费推理：成本与时长估算

### 4.1 单集假设（来自自构 transfer smoke 量级，Lite 可能略高）

| 量 | 保守 | 中位 | 偏高 |
| --- | ---: | ---: | ---: |
| prompt/集 | 12k | 18k | 30k |
| completion/集 | 6k | 11k | 20k |
| 墙钟/集（2 步×3 臂混） | 60s | 90s | 150s |

### 4.2 正式 90 集

| 档 | Prompt | Completion | **合计 token** | **推理墙钟** |
| --- | ---: | ---: | ---: | ---: |
| 低 | 1.08M | 0.54M | **≈1.6M** | ≈1.5 h |
| **中（建议按此备）** | **1.62M** | **0.99M** | **≈2.6M** | **≈2.3 h** |
| 高 | 2.70M | 1.80M | **≈4.5M** | ≈3.8 h |

加评测 0.3h → **总墙钟中位约 2.5–3 h**。

### 4.3 与「之前的实验」对比

| 实验 | 规模 | Token |
| --- | --- | --- |
| 原 V13E DS 全量 | 1176 eps × 7 臂 | **6.55M** |
| 原 V13E 双模型 | 2352 eps | **11.4M** |
| **本 P1 Lite DS** | **90 eps × 3 臂** | **≈2.6M（中位）** |

→ **约原 DS 单模型的 40%、双模型的 23%**；与你说的「差不多、略多一点」相比，**实际更省**（因只 DS + 3 臂 + 10 题）。

---

## 5. 开跑前仍缺（需你一句确认）

1. **确认付费全量 90 集**（DeepSeek，中位 ≈2.6M tokens / ≈2.5–3h）  
2. runner 接 SWE-bench 任务集（`tasks_swebench_lite`）+ Docker eval 串联 — 我在开跑前接完  
3. 未确认前 **不发** 付费请求  

---

## 6. 产物

| 路径 | 内容 |
| --- | --- |
| `data/eval_gold_docker_all.json` | gold 10/10 |
| `tasks_swebench_lite/` | 10 题工作区 |
| 本文件 | 统计字段 + 估算 |
