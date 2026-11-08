# V1.3 M2-Revision-Fix Review 报告

性质：**独立只读审查**。未改任何文件；未跑模型；无 Git 写。  
对象：rev3、revision_fix_response、rev2、原计划、revision_review_report、V1.2 method/prereg + 实测代码。

---

## 1. 审查范围

| 文件 | 读取 |
| --- | --- |
| `v13_m2_validation_plan_rev3.md` | 完整 248 行 |
| `v13_m2_revision_fix_response.md` | 完整 |
| rev2 / 原计划 / revision_review | 完整/关键节 |
| `p1_common.py` / `build_messages` / `SYSTEM_PROMPT` | **实测** |
| prereg bootstrap seed | 实测 |
| `run_p1_v12.py` 字段来源 | 只读 grep |

---

## 2. R1–R6

### R1 Bootstrap seed — **PASS**

| 项 | 实测 | 结论 |
| --- | --- | --- |
| prereg seed | `20261102` | 冻结源 |
| rev3 bootstrap | §3.3/§4.3 **20261102** | **一致** |
| B | 10000 | 一致 |
| 聚类 | task_id | 一致 |
| 随机化 seed 20261103 | §3.3 **仅 episode 排序** | 与 bootstrap **用途分离**，已写明 |

### R2 S7 — **PASS（方案 B）**

- §5.2/§5.2.2：S7 **不参与自动停止**；仅描述统计。  
- S1–S6 与原计划/rev1 数值一致（安全、磁盘、泄漏、失败率&gt;50%、2× token、ESR−0.10∧TPAE≥F）。  
- hit/touch 单位 = **adaptive_audit 行（文件×步）**。  
- 禁止写成检验通过/失败。 **PASS**

### R3 Prompt 冻结 — **PARTIAL**

| 项 | 文档声明 | 实测 | 结论 |
| --- | --- | --- | --- |
| SYSTEM_PROMPT | `4f591635…dca01a` | **相同** | **PASS** |
| `build_messages` 源码 | `f0b477b0…9e436` | **相同**（inspect.getsource） | **PASS** |
| `p1_common.py` 整文件 | rev3 写 **`70784d9c…`** | bytes= **`e32fd305…`** | **FAIL（文档错误）** |
| 同上（fix_response） | **`e32fd305…`** | 与 bytes 一致 | **PASS** |
| 消息顺序 | history+user；system→assistant→user | 与 `build_messages` 源码一致 | **PASS** |
| history=keep | trim 24000；不切 redact | 与 runner 一致 | **PASS** |
| FILE 注入 | user CONTEXT `--- FILE` | 与 runner 一致 | **PASS** |

**根因**：`70784d9c…` 来自 `read_text().encode()`（换行规范化），与 `read_bytes()` 不同。  
**问题**：rev3 正文与 fix_response **互相矛盾**；若按 rev3 校验会误判不一致。

**结论：PARTIAL。** 哈希机制与 SP/BM 正确；**必须更正 rev3 第 63 行** 为 bytes 哈希后再冻结。

### R4 字段字典 — **PASS**

| 字段 | 代码/日志证据 |
| --- | --- |
| eval_success / tokens / context_* / must_full_count / edit_targets / insufficient / error | `run_p1_v12` result 写出 **PASS** |
| pre_send_check.ok / omitted | `pre_send_check.json` **PASS** |
| adaptive_audit | `plan.audit()` → injection_audit **PASS**（非 result 顶层；字典已写 plan 来源） |
| DHO | **派生** omitted∩edit_targets；缺 audit→NA **PASS**（标注导出，可确定性重建） |
| Full/Digest/None | context 计数 **PASS** |

原生 vs 派生已区分；未把未实现字段写成原生。 **PASS**

### R5 错误分类 — **PASS**

§4.5 四类矩阵完整；默认 **不剔除** task/失败样本；协议≠架构；待决项（人工重跑）不默认允许。 **PASS**

### R6 窗口与状态 — **PASS**

- S4：**全 run**；失败 episode/尝试 episode。  
- 状态：PASS/FAIL/NOT_TRIGGERED/NOT_APPLICABLE/INSUFFICIENT/NA。  
- NOT_TRIGGERED≠PASS；NA≠0。 **PASS**

---

## 3. 哈希实测汇总

```text
SYSTEM_PROMPT     4f59163597ba6982b2f77d2571792b3883198632b7cc9e8cd9ce297218dca01a
build_messages    f0b477b0046282739ba1309e5035b2beb2f2f8d2564535d7154019a9aee9e436
p1_common bytes   e32fd30517322e8976c8f7710be69fae508c9957a926079c526f9468a3f384f2
rev3 plan         ff070114d7388b95f3762c8221a8f297a7f2909ecc6b0dece8a1cbba2fcd355a
```

---

## 4. 全局一致性 — **PASS**

V13A 规则、E/F/V13A、12 holdout、R=2、72/144、Q6_K、安全 O′/ET/must/INSUFFICIENT、ESR/TPAE/TPSE 阈值、无额外调用/重试/反馈 — **均未变**。  
rev1→rev2→rev3 继承清晰；**唯一正文冲突**为 rev3 的 p1_common 哈希 vs fix_response。

---

## 5. 未解决风险

| 级别 | 项 |
| --- | --- |
| **冻结前必须改** | rev3 §3.1.1 `p1_common.py` 哈希改为 `e32fd305…`（或标注 bytes 口径并删除错误值） |
| 非阻断 | Holdout 未建；DHO 导出脚本；R=2 功效 |
| 非阻断 | architecture 仍无 per-episode adaptive 字段在 result 顶层（在 injection_audit） |

---

## 6. 最终结论

# CONDITIONAL PASS

**关闭 R1、R2、R4、R5、R6；R3 因 rev3 正文 p1_common 哈希错误 PARTIAL。**

### 进入 M2-Holdout Freeze 审批前必须

1. **更正** `v13_m2_validation_plan_rev3.md` 中 `p1_common.py` 哈希为 bytes 实测值 **`e32fd30517322e8976c8f7710be69fae508c9957a926079c526f9468a3f384f2`**（或删除该行并只保留 response 中已验证值，但须两文一致）。  
2. 更正后重算 rev3 SHA256。

**本审查不授权 Holdout Freeze。**

---

## 7. 本报告信息

- 路径：`p1/experiments/v12_p1_execution/v13_design/v13_m2_revision_fix_review_report.md`  
- Git：`p1/v1.1` @ `155f934bc6c565bd304b2b7438259d592bc348c8` · stash 未动 · 无写操作  
