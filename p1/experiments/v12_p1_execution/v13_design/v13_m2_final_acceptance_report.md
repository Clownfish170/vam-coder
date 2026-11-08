# V1.3 M2 最终只读验收报告（M2-Final Acceptance）

性质：**只读**。未改文件；未跑模型/实验/Holdout；无 Git 写；**不宣布 Holdout Freeze 获批**。  
哈希计算：文件 = `hashlib.sha256(Path.read_bytes())`；SYSTEM_PROMPT = UTF-8 字符串 encode；`build_messages` = `inspect.getsource().encode()`。

---

## 1. 检查文件清单

| # | 文件 | 状态 |
| --- | --- | --- |
| 1 | `v13_m2_validation_plan_rev3.md` | 已读/已测哈希 |
| 2 | `v13_m2_revision_fix_response.md` | 已读 |
| 3 | `v13_m2_revision_fix_review_report.md` | 已读 |
| 4 | `v13_m2_validation_plan_rev2.md` | 存在 |
| 5 | `v13_m2_validation_plan.md` | 存在 |
| 6 | `v1.2_method_formulation.md` / `experiment_preregistration.md` | 存在（seed 交叉） |
| 7 | `p1/scripts/p1_common.py` | **实测 bytes** |
| 8–9 | SYSTEM_PROMPT / build_messages | **实测** |

---

## 2. 哈希实测

| 项 | 实际值 | 期望值 | 结果 |
| --- | --- | --- | --- |
| **R1** p1_common.py bytes | `e32fd30517322e8976c8f7710be69fae508c9957a926079c526f9468a3f384f2` | 同 | **PASS** |
| rev3 含正确哈希 | 是 | 是 | **PASS** |
| rev3 无旧错 `70784d9c…` | 是 | 是 | **PASS** |
| rev3 标明 read_bytes | 是 | 是 | **PASS** |
| **R2** rev3 文件 SHA256 | `8ceed45d6554ba952a641fbbebb49b4f3eb0f69858c16ba9d58d7025eb9ee13f` | 同 | **PASS** |
| **R3** SYSTEM_PROMPT | `4f59163597ba6982b2f77d2571792b3883198632b7cc9e8cd9ce297218dca01a` | 同 | **PASS** |
| **R3** build_messages 源码 | `f0b477b0046282739ba1309e5035b2beb2f2f8d2564535d7154019a9aee9e436` | 同 | **PASS** |

---

## 3. R1–R6 验收表

| 项 | 结果 | 证据摘要 |
| --- | --- | --- |
| **R1** p1_common 哈希修复 | **PASS** | bytes=期望；rev3 已更正；无旧值 |
| **R2** rev3 SHA256 | **PASS** | `8ceed45d…ee13f` |
| **R3** 其他关键哈希 | **PASS** | SP/BM 与期望一致 |
| **R4** 设计/实验约束无漂移 | **PASS** | bootstrap 20261102+B=10000+task cluster；随机化 20261103 仅顺序；S7 仅诊断；V13A/E/F；12 holdout、R=2、72/144；禁旧 24 冒充；S1–S6/失败率/状态枚举/协议≠架构 均在 |
| **R5** 文档一致性 | **PASS** | rev3 与 fix_response 哈希一致；rev2/原计划未改；无“已复跑/已实验”虚假陈述 |
| **R6** Git 保护 | **PASS** | branch `p1/v1.1`；HEAD `155f934bc6c565bd304b2b7438259d592bc348c8`；stash@{0} 存在；本验收无新文件修改 |

自动核验合计：**35/35 PASS**（见执行记录）。

---

## 4. 哈希计算方式

```text
p1_common.py     sha256(Path.read_bytes())
SYSTEM_PROMPT    sha256(SYSTEM_PROMPT.encode('utf-8'))
build_messages   sha256(inspect.getsource(build_messages).encode('utf-8'))
v13_m2_*         sha256(Path.read_bytes())
```

---

## 5. 未解决问题与风险

| 级别 | 项 |
| --- | --- |
| 非本验收范围 | Holdout 任务尚未创建；真实模型实验未跑 |
| 计划内已知 | R=2 探索性；DHO 依赖导出脚本；S7 仅诊断 |
| 无 | 本哈希阻断项 **已关闭** |

---

## 6. 最终结论

# PASS

**含义**：M2-Hash-Fix 已修复最后阻断项；`v13_m2_validation_plan_rev3.md`  
**可作为 Holdout Freeze 审批的候选版本**。

**明确不表示**：

- Holdout Freeze 已批准；  
- 允许运行任何实验；  
- 允许建任务或 Git 写操作。

**等待你对 Holdout Freeze 的单独决定。**
