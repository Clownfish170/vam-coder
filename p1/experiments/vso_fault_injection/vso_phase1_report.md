# VSO 专项 Phase1 报告：安全省略边界与故障注入（无模型 harness）

状态：**Phase1 完成，联合判定 PASS**。设计冻结：`vso_fault_injection_evaluation_design.md` v2（sha `0d9c292b2ef7e09fc0d6ddef137d163ca91a342c1e8144341fce3d3725f1746b`）。  
产物：`scenario_matrix.csv`（31 场景）、`vso_harness.py`、`vso_results.csv`、`vso_summary.json`。全程未修改任何生产代码（`p1/scripts/`、`src/` 只读），无模型请求。

---

## 1. 样本构成（与冻结矩阵一致）

| 类别 | 数量 | 内容 |
| --- | ---: | --- |
| 负向不安全省略 | 13 | V1–V5（可见性）、C1–C3（约束预算）、H1–H5（历史完整性，H4 含 attempted/final DHO） |
| 正向安全省略 | 9 | P1–P9（互异条件：近期/跨步可见、多文件批、混合批、**动态重验证 P5**、回写、O′ 正常、长历史、must 邻接） |
| 假阻断对照 | 8 | FP1–FP8（独立合成文件的无故障正向实例） |
| 边界受控 | 1 | C4（预算仅超可选 → 允许省略仅限可选，must 保留） |
| **合计** | **31** | 每场景含：初始状态 / 注入方式 / 预期行为 / expected_decision / B1·B2·VSO 预期 / 机器可检条件 |

**端到端装配路径子集（冻结五场景）**：V4、V1、C1、C3、H1 —— 走真实 `plan → assemble → build_messages → verify_omissions_in_messages → 门闩` 全链，断言落在**实际最终 messages** 上（非中间结构）。

## 2. 五指标结果（预冻结阈值联合判定）

| 指标 | 结果 | 阈值 | 判定 |
| --- | ---: | --- | --- |
| **UOR**（不安全省略率） | **0.00**（0/13） | = 0 | ✅ |
| **SOR**（安全省略率） | **1.00**（10/10，含 C4 边界） | ≥ 0.8 | ✅ |
| **FBR**（错误阻断率） | **0.00**（SOR+FBR≡1 恒等核验） | ≤ 0.1 | ✅ |
| **FSR**（回退成功率） | **1.00**（13/13 负向均正确回退/阻断且交付不变量成立） | ≥ 0.9 | ✅ |
| **联合判定** | **PASS**（UOR=0 ∧ SOR≥0.8 ∧ FBR≤0.1 ∧ FSR≥0.9） | — | ✅ |

附加：**Decision Accuracy = 31/31 = 1.00**；`attempted_dho_sum = 1`、`final_dho_sum = 0`（H4 注入生效且按冻结 DHO 公式归零）；B1/B2 预期吻合 31/31。

## 3. 三机制对照（创新性判据核心）

| 机制 | EDR（V1–V5 五场景检出率） |
| --- | ---: |
| **VSO** | **1.00（5/5）** |
| B1 普通内容 Hash Check | 0.00（0/5） |
| B2 Cache Consistency Check | 0.80（4/5） |
| **VSO 独占检出** | **1（V4）** |

- **V4（内容没变但不在最终 messages）**：B1 授权（磁盘自洽）、B2 授权（该 sha 曾发送）→ **只有 VSO 经最终 `verify_omissions_in_messages` 拦截并回退全量**——机制差异的直接证据，正是冻结设计要求保真的核心区分场景。
- B1 在可见性故障上 0 检出符合其机制边界（内容完整性 ≠ 可见性），未被人为削弱；B2 凭"曾发送"拦下 V1/V3/V5 类，但对 V4 的"发过 ≠ 还在"盲区如实暴露。
- 约束层（C）与历史层（H）超出 B1/B2 的职责范围（矩阵标注 NA/按内容判），VSO 在 C1/C3/H1–H5 全部按 expected 处置。

## 4. 关键场景执行摘要（`vso_results.csv`）

| 场景 | expected → observed | 机制要点 |
| --- | --- | --- |
| V4 | FORCE_FULL ✓ | 候选层放行（tracker 有证明）→ 最终验证 `not_in_final_messages` 拦截 → force_full 修订后通过（e2e） |
| C3 | INSUFFICIENT ✓ | required 9000 > window 8192 → 不发请求（预算耗尽 ≠ 可省略）（e2e） |
| H4 | FORCE_FULL ✓ | attempted_dho=1 → 回退后 final_dho=0（冻结公式） |
| P1–P9 | ALLOW_OMISSION 全数 ✓ | 无一正向被误阻断（含动态重验证 P5、20 条长历史 P8） |
| FP1–FP8 | ALLOW 全数 ✓ | 假阻断率 0 |

## 5. 边界与声明

1. Phase1 为**确定性 harness 结论**：证明安全逻辑在注入故障下的行为，不涉及模型交互——真模型链路确认属 Phase2（冻结场景 `V1,V4,C1,C2,C3,H1,H2,V5,P1,P5` ×R3，DeepSeek，尚未启动）。
2. UOR=0/SOR=1.0 是**本矩阵31 场景内**的结果；0.8/0.1/0.9 为预冻结工程验收阈值，不构成"VSO 已充分安全"的科学结论（冻结设计 §3.4 条款）。
3. 测试侧注入清单见 `vso_harness.py`（各 run_* 函数）；生产代码零修改（如未来发现必须改生产代码 → 按冻结设计 §6 暂停报告）。
4. 断点/执行中修复记录：harness 迭代中的接口适配（mark_from_assistant 入参、reasons list 语义）均属测试侧修正，未触碰生产文件。

## 6. 下一步（Phase2）

按冻结设计 §4：DeepSeek 主模型、10 场景 × R3 = 30 集、确认性定位（不做显著性/泛化结论）；实现方式为**进程内 monkeypatch 包装 runner**（测试侧，不改生产代码），验证故障在真实执行链路中仍被正确处置。完成后与本 Phase1 合并出 `vso_report.md`。
