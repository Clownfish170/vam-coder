# M2-Plan Revision Response

对应审计：`v13_m2_review_report.md`（CONDITIONAL PASS）  
修订交付：`v13_m2_validation_plan_rev2.md`  
原计划：`v13_m2_validation_plan.md` **未修改**。

---

## 1. P1 逐项关闭情况

| ID | 要求 | rev2 落点 | 关闭？ |
| --- | --- | --- | --- |
| P1-01 | §5.3 与 §7 停机一致；升级率不悬空 | §5.2 **S1–S7** 并入原 §7 条件；**S7 不写新数字阈值**，用“与 E/F 分布不可区分 + hit/touch 无解释”定义 | **是** |
| P1-02 | task 聚类 | §4.3：聚类单位=task_id；B=10000 seed=20261103；**方法沿用 P1**（非新检验） | **是** |
| P1-03 | 可复现 prompt | §3.1.1：SYSTEM_PROMPT **全文哈希** `4f591635…dca01a` + `build_messages` 模板锁定；不一致停 | **是** |
| P1-04 | per-step 字段 | §3.3.1 完整文件与 result 字段表 | **是** |
| P1-05 | 三臂同源 | §2.3 同一 `project/` copy 规则 | **是** |
| P1-06 | Prefill | §3.4.1 主指标=prompt_tokens；cached 分列 | **是** |
| P1-07 | NA 规则 | §3.4.2 指向 method/prereg，不第三定义 | **是** |
| P1-08 | NOT_TRIGGERED≠PASS | §4.4 | **是** |
| P1-09 | 协议≠架构 | §4.4 | **是** |
| P1-10 | 失败率口径 | §5.2 S4 口径说明（**无新百分比门**） | **是** |

---

## 2. 是否擅自创造新规则？

| 项 | 结论 |
| --- | --- |
| V13A 算法 | **未改** |
| 臂 E/F/V13A、样本量原则 12×3×R2 | **未改** |
| 安全门槛 / 效果门槛数值（0.05 等） | **未改** |
| 停止条件 S6/S7 | **原 §7 原文条件**，仅并入 §5.2 执行表 |
| 升级率/失败率数字阈值 | **未新增**；S4/S7 用口径定义 |
| 统计检验 | **沿用 P1 task-cluster bootstrap**，非新检验 |
| 重试规则 | **仍禁止自动重试** |

---

## 3. 是否牺牲原实验设计？

**否。** Holdout 12/8、随机化、环境参数、安全一票否决、探索性措辞均保留。

---

## 4. 指标是否可从日志计算？

| 指标 | 日志源 |
| --- | --- |
| ESR/SPR | eval_success |
| TPAE/TPSE/FETC | result tokens |
| Prefill | prompt_tokens（usage） |
| Full/Digest/None、升级率、adaptive_audit | result/context/injection_audit |
| 安全 DHO/INSUFFICIENT/must | pre_send + audit + result |
| task 聚类 CI | per_step + task_id |

**无**依赖模型未提供字段；cached 仅分列。

---

## 5. 未改文件

- `v13_m2_validation_plan.md`（原）  
- 代码、V1.2 冻结文档、任务集、Git  

---

## 6. 结论

**rev2 已针对 P1-01～P1-10 写入可执行、可复现的冻结条款；未改 V13A/臂/样本量/安全门槛。**  

提交 `v13_m2_validation_plan_rev2.md` + 本文件，等待 **M2-Revision Review**。
