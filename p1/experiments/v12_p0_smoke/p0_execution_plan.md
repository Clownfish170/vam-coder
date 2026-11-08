# V1.2-r2.2 P0 Smoke 执行计划（阶段 B）

状态：**计划编制完成 · 未获真实模型执行授权**。  
目录：`p1/experiments/v12_p0_smoke/`

---

## 1. 实验目的

验证已验收 M1–M4 / M3-FIX-01 在 **真实模型** 下的注入、O′、EditTarget/CandidateFull 与请求前阻断行为。  
**不是** P1 正式实验，**不做**统计显著性。

---

## 2. 范围（已锁定，不得擅自改）

| 项 | 值 |
| --- | --- |
| 任务 | 8：IRR01, CFD01, DUP01, DEL01, RUR02, RFS01, RUR03, STM02 |
| Arms | **E, F, G, H**（本轮 **无 D**） |
| R | **1** |
| Episodes | **32** |
| 理论请求上限 | **64**（32×2 steps）——**非**必须完成数 |
| P1 / R=3 / 显著性 | **不做** |

---

## 3. Arms（r2.2）

| Arm | 非目标策略 |
| --- | --- |
| E | 相关 → Digest，无关 → NONE |
| F | 相关 → Full，无关 → NONE |
| G | 关 task-aware；非 must 按 full_if_indexed；must 不变 |
| H | 非目标全 NONE |

**全臂不变**：E/C 强制 FULL；Negative 不进 EditTarget；O′ 可见性；INSUFFICIENT；不静默截断；d=2；Kmax=8。

---

## 4. 任务集

- 源：`p1/tasks/tasks_v1.0.json` + `p1/tasks/<id>/project`  
- 明细：`task_mapping.csv`（EXPECTED_TRIGGER / NOT_EXPECTED / UNCERTAIN 分列）  
- **禁止**改任务、造任务；未触发机制 → **NOT_TRIGGERED**（≠ PASS）

---

## 5. Episode 隔离

- 每个 `episode_id = {task}_{arm}_R1`  
- 初始工作区：从冻结 `project/` **独立 copytree**（见 `episode_manifest.json` 的 `initial_workspace_hash`）  
- Arm 间 **不共享** 修改；step2 **仅** 使用本 Episode step1 后的 workspace  
- 禁止跨 Episode 污染  

---

## 6. 随机化

| 项 | 值 |
| --- | --- |
| 种子 | **20261102** |
| 方法 | `random.Random(seed).shuffle` |
| 清单 | `randomization_manifest.json`（original + randomized + uniqueness_check） |
| 约束 | 每 Episode 恰一次；不得按结果改序 |

随机化 **不** 赋予统计推断能力。

---

## 7. 失败与计数规则

1. **INSUFFICIENT**：记 episode 已启动；分别统计 **INSUFFICIENT episodes / blocked requests / actual model requests**。  
2. **Step1 失败**：按原任务定义；若定义不允许 step2 → `NOT_EXECUTED`。  
3. **Step2 失败**：Episode 失败，不得只留 step1 成功。  
4. **协议违规**：保留原始输出与类型，禁止自动修复覆盖。  
5. **评估失败**：保留 output / diff / eval。  
6. **NOT_TRIGGERED** ≠ 机制验证成功。  
7. **请求次数** = 实际 `chat_completion` 调用数。  
8. **禁止**自动重试刷成功率。  
9. **禁止**运行中人工改模型文件。  
10. **中断**：保存进度，禁止伪造未执行结果。

---

## 8. 日志要求（每 Episode×Step）

`request/response/context/pre_send_check/injection_audit/evaluation` + token/prefill、EditTargets、CandidateFull、Excluded、must_full、O′、协议违规、错误。

---

## 9. 停止条件（任一即停）

冻结哈希变化；HEAD/stash 异常；模型配置不符；**验证失败仍发模型请求**；E/C 未强制 FULL；O′ 误省必须文件；缺文件无 INSUFFICIENT；超窗静默截断；结果无法追溯；未授权改码/资产。

模型自身 NO_EDIT/推理失败 → **记录**，不重试到成功、不改算法。

---

## 10. 结果解释边界

- 仅 **Smoke 验证**；样本不足 → **禁止** 称统计显著或 SCI 假设成立。  
- ESR/SPR/Token 可算，但 **不作** 门禁放行依据（门禁属 P1 预注册）。

---

## 11. 配置（prereg）

Q6_K · llama-server · ctx=8192 · parallel=1 · seed=0 · temperature=0 · max_tokens=1024 · history=keep · d=2 · Kmax=8。

---

## 12. 授权状态

| 阶段 | 状态 |
| --- | --- |
| A Preflight | 通过 |
| **B 执行计划** | **本文件** |
| C 真实模型 P0 | **未授权** |
| P1 | **不授权** |

**阶段 B PASS ≠ 阶段 C 授权。**
