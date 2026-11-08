# VSO 专项实验终报告：安全省略边界与故障注入（Phase1 + Phase2）

状态：**两阶段完成，联合判定 PASS**。  
设计（冻结）：`p1/docs/vso_fault_injection_evaluation_design.md` v2，sha256 `0d9c292b2ef7e09fc0d6ddef137d163ca91a342c1e8144341fce3d3725f1746b`。  
定位：安全机制验证（不比较架构 ESR/token、不做跨任务泛化；Phase2 为逐场景确认性断言，不做显著性）。

---

## 1. 两阶段总览

| 阶段 | 内容 | 规模 | 模型 | 生产代码 |
| --- | --- | --- | --- | --- |
| Phase1 | 函数级故障注入 + 哈希/缓存基线对照 + 五场景端到端装配路径 | 31 场景（13 负 +9 正 +8 对照 +1 边界） | 无模型 | **只读** |
| Phase2 | 冻结 10 场景嵌入真实执行链路（进程内 monkeypatch 包装 runner） | **30 episodes（10×R3）** | DeepSeek `deepseek-v4.1-flash-1017`（与 P1/P2 同源） | **只读（production_code_modified=false，run 内记录）** |

## 2. Phase1 五指标（预冻结阈值联合判定）

| 指标 | 结果 | 阈值 | 判定 |
| --- | ---: | --- | --- |
| UOR 不安全省略率 | **0.00（0/13）** | =0 | ✅ |
| SOR 安全省略率 | **1.00（10/10 含 C4 边界）** | ≥0.8 | ✅ |
| FBR 错误阻断率 | **0.00**（SOR+FBR≡1） | ≤0.1 | ✅ |
| FSR 回退成功率 | **1.00（13/13）** | ≥0.9 | ✅ |
| **联合判定** | **PASS** | — | ✅ |

辅助：Decision Accuracy 31/31；`Σattempted_dho=1 → Σfinal_dho=0`（冻结公式）；B1/B2 预期吻合 31/31。

**三机制对照（核心）**：EDR@V1–V5 = **VSO 1.00 / B1 0.00 / B2 0.80**；**VSO 独占检出 = 1（V4：内容没变、曾发送过，但不在最终 messages——B1/B2 双双授权，只有 VSO 拦下）**。Phase1 e2e 五场景（V4/V1/C1/C3/H1）在真实 plan→assemble→build_messages→verify 全链上断言通过。

## 3. Phase2 结果（`phase2_runs/`）

| 场景 | expected | observed（3/3 一致） | 激活证据 |
| --- | --- | --- | --- |
| V1 过期证明 | FORCE_FULL | FORCE_FULL ✅×3 | 注入步前模型已回写 `inventory.py`（自然证明存在）→ 全程 EXPAND、省略=0（故障因果成立） |
| **V4 核心区分** | FORCE_FULL | FORCE_FULL ✅×3 | 候选层放行 → 最终验证拦下 → **revised=3/3**（真实回退） |
| C1 must 冲突（破损授权器） | FORCE_FULL | FORCE_FULL ✅×3 | broken_auth 注入 3/3、revised=6（10 步中 6 步触发回退）、unsafe=0、must 全在最终 messages |
| C2 target 冲突（破损授权器） | FORCE_FULL | FORCE_FULL ✅×3 | 同上注入；edit_target_full_verified 全真、DHO=0 |
| C3 预算耗尽 | INSUFFICIENT | INSUFFICIENT ✅×3 | insufficient 步=6、**requests=0**（未发模型请求） |
| H1 损坏历史 | FORCE_FULL | FORCE_FULL ✅×3 | 证明哈希被注入为 CORRUPT → 拒绝省略 → 回退（因果同 V1：自然证明存在却零省略） |
| H2 不可恢复历史 | FORCE_FULL | FORCE_FULL ✅×3 | 抹围栏致证明不可解析 → 同上 |
| V5 外部覆盖 | FORCE_FULL | FORCE_FULL ✅×3 | `inventory.py` 过期证明 → 5 步全 EXPAND；他处合法省略仍工作（reuse=1, pricing.py） |
| P1 正向近期可见 | ALLOW_OMISSION | ALLOW_OMISSION ✅×3 | reuse=3，unsafe=0 |
| P5 正向动态重验证 | ALLOW_OMISSION | ALLOW_OMISSION ✅×3 | reuse=9（5 步任务），按当前内容重证明后省略 |

**汇总：30/30 episodes、decision_accuracy=1.00、10/10 场景 PASS、unsafe_ship=0、dho=0。**

执行审计（如实披露）：
1. 任务映射修正：首轮 6 场景落在"省略不可达"任务上（判定虽对但注入未激活）——18 条记录**归档保留**于 `phase2_runs/execution_log_superseded_vacuous.jsonl`（未删除），修正映射后在可激活任务（p1_M01a/p1_L01b）重跑至激活。
2. 断言两处过严（C1 曾按"must 不得被省略"与"终局磁盘哈希比对"判定）→ 按**冻结文档字面**（"must 出现在最终 messages"+RSR 口径）修正后复评；期间**未重跑任何模型请求**（仅重新评估既有 30 集产物）。
3. `fault_safe_calls` 字段因离线复评丢失（记为 N/A）；激活判定改用行为证据（echo 对比 / revise / reuse / insufficient 计数），见上表。

## 4. 结论（对核心问题的回答）

1. **当系统无法证明必要信息已安全交付时，VSO 能阻止省略并正确回退/阻断吗？** —— Phase1 UOR=0/FSR=1 + Phase2 十场景 30/30：**能**；含端到端真实链路（V4 的候选放行→终验拦截→force_full 回退被真实观测 3/3）。
2. **VSO 相比普通哈希/缓存一致性多提供了什么？** —— V4 上 B1/B2 双双授权、唯一由 VSO 拦截（独占检出=1）；B1 在全部可见性故障上 0 检出（其机制边界如实呈现，未削弱）；B2 盲区 = "发过 ≠ 还在最终 messages"。
3. **防"全不省略"刷分？** —— SOR=1.0（9 正向+1 边界全部正常省略，含动态重验证 P5），FBR=0。

## 5. 局限

- 31+30 是**受控场景**证据，不是自然故障率；不外推"生产环境中 VSO 覆盖所有风险"。
- Phase2 无显著性检验（冻结定位为确认性）；单模型（DeepSeek）；Qwen 跨模型扩展按设计留待后续。
- Phase1 断言与冻结文档字面一致处曾有两处偏差已修正（见审计2），过程完整可复盘（代码 git-less 但文件时间线+superseded 记录在档）。
- 0.8/0.1/0.9 为工程验收阈值，非充分安全性证明（预注册 §3.4 条款）。

## 6. 交付物

| 文件 | 内容 |
| --- | --- |
| `p1/docs/vso_fault_injection_evaluation_design.md` | 冻结设计 v2（sha `0d9c292b…`） |
| `scenario_matrix.csv` | 31 场景六要素 + expected + B1/B2 预期 + e2e/phase2 标记 |
| `vso_harness.py` + `vso_results.csv` + `vso_summary.json` | Phase1 全量结果 |
| `phase2_runs/vso_phase2_results.csv` + `vso_phase2_summary.json` | Phase2 逐集结果与判定 |
| `phase2_runs/execution_log_superseded_vacuous.jsonl` | 映射修正前 18 条记录（归档保留） |
| 本报告 | `vso_report.md` |

追溯：Phase1 按 scenario_id；Phase2 按 `episode_id = {task}_{scenario}_R{rep}` → `phase2_runs/runs/<id>/runner_out/...`。
