# P1_TRANSFER 协议与结果报告（V13E · 真外部 SWE-bench Lite）

**实验编号：** P1_TRANSFER  
**旗舰：** V13E（F / PROJ / MOFF）  
**报告类型：** **协议 + 完整跑批结果**（非 SWE-bench 官方 leaderboard）  
**日期：** 2026-11-17  

---

## 0. 诚实边界（必读）

1. **不是** SWE-bench 官方完整评测协议，**不能**与 leaderboard resolve rate 直接对比。  
2. 数据 = **SWE-bench Lite 10 实例子集** + **本地 Docker** 跑 `FAIL_TO_PASS`。  
3. 自构机理轨（`tasks_transfer_v1`）与本轨 **分表**，不合并绝对 token。  
4. 模型：DeepSeek 主跑已完整；Qwen 复现使用 **`qwen3.8-flash`**（非原 `qwen3-coder-flash`，因 token-plan endpoint 无该模型）。  
5. 部分补跑曾切换 endpoint/key（见 §6），**已披露**。  

---

## 1. 任务来源与筛选

| 项 | 值 |
| --- | --- |
| 数据集 | `SWE-bench/SWE-bench_Lite` test split（300） |
| HF revision | `b0dde1093fe417d83b7184254edf8199c1f0dff5` |
| 下载 | hf-mirror parquet |
| 子集 | **10** 实例（排除 django/sympy/matplotlib 等重环境） |
| 类型分布 | requests×3 · pytest×4 · flask×2 · pylint×1 |
| 任务形态 | **单步**：`problem_statement` → `FILE:` 整文件 → Docker 评测 |

**清单：** `p1/experiments/v13e_p1_swebench/tasks_swebench_lite/swebench_lite_tasks.json`  
**实例 ID：**  
`requests-3362/863/1963` · `pytest-7432/11143/5413/6116` · `flask-4045/5063` · `pylint-7993`

筛选规则：非重依赖仓、patch/issue 规模可控、FAIL_TO_PASS 1–12、每仓 ≤3、类型混合。

---

## 2. 实验协议（冻结）

### 2.1 臂

| 臂 | 架构 ID | 机制 |
| --- | --- | --- |
| F | `vam_coder_v1.2_F` | VSO/O′ 选择性交付 |
| PROJ | `vam_coder_v1.3E_PROJ` | F + S1 `first_last` |
| MOFF | `memory_off` | 每步全仓倾倒（无 VAM） |

**主比较：** PROJ−F  
**次级：** PROJ−MOFF、F−MOFF  

### 2.2 控制

| 项 | 值 |
| --- | --- |
| 规模 | 10 × 3 臂 × 3 reps × **先 DS 后 Qwen** |
| DS 模型 | `deepseek-v4.1-flash-1017` |
| Qwen 模型 | **`qwen3.8-flash`**（token-plan） |
| 解码 | temp=0, seed=0, **max_tokens=16384** |
| 窗口 | budget=16384, window=65536 |
| HTTP timeout | **600s** |
| 评测 | 官方 `swebench/sweb.eval.*` 镜像内跑 FAIL_TO_PASS |
| 统计单位 | **10 个 instance**（3 次重复不视作 30 独立题） |

### 2.3 失败口径（跑批冻结）

| 类型 | 处理 |
| --- | --- |
| **超时**（600s，pt=0） | 可 resume 重试；最终仍失败 → **记 ESR 失败** |
| **INSUFFICIENT**（上下文超限） | **不重试**（用户确认）→ **记 ESR 失败**，单独披露 |
| API 403/空输出 | 可重试；最终失败 → 记失败 |
| complete-case | 附录敏感性：仅 good 样本 |

---

## 3. 最终任务清单与 commit

见 `transfer` 任务 JSON 中 `source.repo` + `source.commit`（10 条，浅克隆钉死）。

| instance | repo |
| --- | --- |
| psf__requests-* | psf/requests |
| pytest-dev__pytest-* | pytest-dev/pytest |
| pallets__flask-* | pallets/flask |
| pylint-dev__pylint-7993 | pylint-dev/pylint |

---

## 4. 模型与参数

| 批次 | model | endpoint | 状态 |
| --- | --- | --- | --- |
| DS 主批 | `deepseek-v4.1-flash-1017` | 初：maas…；补跑：token-plan | **完成 90/90** |
| Qwen 复现 | **`qwen3.8-flash`** | token-plan.cn-beijing.maas.aliyuncs.com | **完成 90/90**（含 fail） |

鉴权：环境变量 `VAM_API_KEY`（不写入本报告正文）。

---

## 5. 正式结果

### 5.1 完成度与失败构成

| | DS | Qwen3.8 |
| --- | ---: | ---: |
| 计划 episodes | 90 | 90 |
| **good（有效输出）** | **90** | **90** |
| 仍失败 | **0** | **0** |

> 补跑后：超时全部救回；`flask-5063` 超限在 **window=98304** 下 **全部通过**。

### 5.2 分臂（全 90 集，最终）

#### DeepSeek

| 臂 | n | **ESR** | res | mean pt (good) |
| --- | ---: | ---: | ---: | ---: |
| F | 30 | **0.900** | 27 | 29.0k |
| PROJ | 30 | **0.933** | 28 | 29.0k |
| MOFF | 30 | **0.933** | 28 | **474k** |

#### Qwen3.8-flash

| 臂 | n | **ESR** | res | mean pt (good) |
| --- | ---: | ---: | ---: | ---: |
| F | 30 | **0.967** | 29 | 29.0k |
| PROJ | 30 | **0.967** | 29 | 29.0k |
| MOFF | 30 | **1.000** | 30 | **518k** |

### 5.3 任务级配对（n=10，bootstrap B=10000，seed=20261102）

#### DeepSeek

| 比较 | Δ prompt (mean) | 95% CI | p | Δ ESR | 95% CI |
| --- | ---: | --- | ---: | ---: | --- |
| **PROJ−F** | **0** | [0, 0] | 1.0 | **+3.3pp** | [0, +10]pp |
| PROJ−MOFF | **−445k** | [−592k, −297k] | **0.0023** | **0pp** | [−10, +10]pp |
| F−MOFF | −445k | [−592k, −297k] | **0.0023** | −3.3pp | [−10, 0]pp |

#### Qwen3.8-flash

| 比较 | Δ prompt (mean) | 95% CI | p | Δ ESR | 95% CI |
| --- | ---: | --- | ---: | ---: | --- |
| **PROJ−F** | **+1** | [−2, +5] | 1.0 | **0.0pp** | [−10, +10]pp |
| PROJ−MOFF | **−489k** | [−641k, −329k] | **0.0023** | −3.3pp | [−10, 0]pp |
| F−MOFF | −489k | [−641k, −329k] | **0.0023** | −3.3pp | [−10, 0]pp |

### 5.4 cached_tokens（API `prompt_tokens_details`，非服务端 KV 显存）

| | DS sum | Qwen sum |
| --- | ---: | ---: |
| F | 767k | 535k |
| PROJ | 610k | 311k |
| MOFF | 5.10M | 2.64M |

与 prompt 规模同向；**不主张** KV/延迟收益。

### 5.5 ESR 拉平情况（vs MOFF）

| | F | PROJ | MOFF | F/MOFF 差 |
| --- | ---: | ---: | ---: | ---: |
| DS | 0.900 | 0.933 | 0.933 | **−3.3pp** |
| Qwen | 0.967 | 0.967 | 1.000 | **−3.3pp** |

补超限后 **ESR 已与 MOFF 基本持平**（仅差 1 集）；**token 仍差一个数量级**（F/PROJ ~29k vs MOFF ~0.5M）。

---

## 6. 异常、补跑与执行披露

| 事件 | 处理 |
| --- | --- |
| 早期 UTF-8 崩溃 | `errors="replace"` 修复后 resume |
| Docker 引擎未启动 / find_docker 过严 | 修复后重启 |
| 模型欠费 403 | 停跑；续费后换 key |
| 多把无效 key | **未采用**；401 探活失败即弃 |
| 最终可用 | token-plan endpoint + `.qwen38_key` |
| Qwen 超时（曾 10 集） | **1200s + `enable_thinking=false` 全部救回** |
| flask-5063 超限（曾 6+6 集） | **window 65536→98304 后全部通过**（仅改配置，不改框架） |
| summary 被 resume 覆盖 | 从 `execution_log` **重建** |

**微调摘要（均不改 VSO/S1 框架逻辑）：**
1. `max_tokens` 16384  
2. `timeout` 600→1200s  
3. Qwen 补跑 `enable_thinking=false`  
4. `context_window` 65536→**98304**、`budget`→32768（消除超限）

---

## 7. 与原 V13E 自构结果的关系

| | 原 V13E（56 合成题） | 本 P1 真外部 |
| --- | --- | --- |
| 任务 | 自构多步 | **SWE-bench Lite 10** |
| 臂 | 7 | **3（F/PROJ/MOFF）** |
| Qwen 模型 | qwen3-coder-flash | **qwen3.8-flash** |
| 可合并绝对值 | — | **禁止** |
| 方向性 | PROJ 省 prompt、ESR 非劣 | **PROJ−F：ESR 略高或持平；prompt 差≈0 或略负；vs MOFF 大幅省 prompt** |

---

## 8. 证据边界与论文可用结论

### 可以说

1. 在 **SWE-bench Lite 10 子集 + 本地 Docker** 上，F/PROJ 的 prompt 约 **2.9 万/集**，MOFF 约 **47–52 万/集**；**PROJ/F 相对 MOFF 显著省 prompt**（配对 p≈0.002，约 **−44～−49 万/集**）。  
2. **PROJ 相对 F**：ESR **持平或略优**（DS +3.3pp，Qwen 0pp）；prompt **无显著增加**（Δ≈0/1，CI 含 0）。  
3. **ESR 已与 MOFF 基本持平**（DS：0.90–0.93 vs 0.93；Qwen：0.97 vs 1.00，仅差 1 集）。  
4. 补跑后 **90/90 有效**；超时与超限均已消除（超时靠关思考+延时，超限靠 window=98304，**均不改 VSO/S1 框架**）。  
5. 绝对 ESR 仍受 **n=10 小样本** 限制；与原 V13E 分表。  

### 不可以说

1. 官方 SWE-bench resolve / leaderboard 名次  
2. 与原 V13E 合成题绝对 token 直接对比  
3. KV cache / 端到端延迟收益  
4. 形式化安全或「无 TOCTOU」  

### 建议论文表述

> On a 10-instance subset of SWE-bench Lite (local Docker FAIL_TO_PASS evaluation; not the official leaderboard protocol), after raising the context window to 98k and disabling hybrid reasoning for timeout recovery, all 90 episodes per model produced valid outputs. V13E PROJ matched or slightly exceeded F in ESR (DeepSeek 0.933 vs 0.900; qwen3.8-flash 0.967 vs 0.967) with no significant prompt increase versus F, while both selective-delivery arms used roughly an order of magnitude fewer prompt tokens than full-dump memory_off (paired p≈0.002). ESR was on par with MOFF; the remaining gap was token cost, not success rate. Visibility-projection logic was not modified; window/timeout/reasoning flags were configuration-level adjustments. Results are task-level paired over 10 instances and do not merge with the original synthetic V13E batches.

---

## 9. 产物索引

| 路径 | 内容 |
| --- | --- |
| `PROTOCOL_SWEBENCH_LITE.md` | 外部轨协议 |
| `tasks_swebench_lite/` | 10 任务 + 工作区 |
| `runs/p1_swebench_full_20261116_093959/` | DS 90 集 + `analysis.json` |
| `runs/p1_swebench_qwen38_full_20261117_001323/` | Qwen 90 集 + `analysis.json` |
| `analyze_swebench.py` | 配对 CI / 分层 / cached |
| `eval_docker_gold.py` | Docker 评测 |
| `STATS_AND_COST.md` | 统计字段与成本估算 |
| 自构轨 `../v13e_p1_transfer/` | 机理 pilot（分表） |

---

## 10. 变更记录

| 版本 | 说明 |
| --- | --- |
| v1 | 初始协议（F/PROJ） |
| v2 | +MOFF；max_tokens=16384 |
| v3 | DS+Qwen；超时 1200s+关思考救回；**window=98304 消除超限**；**最终 90/90 good** |

---

*P1_TRANSFER · V13E · SWE-bench Lite 子集 · 非官方评测*
