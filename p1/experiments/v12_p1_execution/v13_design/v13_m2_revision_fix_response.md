# M2-Revision-Fix Response（R1–R6）

对应审查：`v13_m2_revision_review_report.md`（CONDITIONAL PASS）  
交付：`v13_m2_validation_plan_rev3.md`（完整计划）+ 本文件。  
**未改** rev2/原计划/代码/任务/Git/模型。

---

## R1 Bootstrap seed 冻结冲突 — **PASS**

| | rev2 | **rev3** |
| --- | --- | --- |
| bootstrap seed | 20261103（错误） | **20261102** |
| B | 10000 | **10000（不变）** |
| 聚类 | task_id | **不变** |
| 依据 | 无变更记录 | **prereg §7 冻结 20261102** |

随机化执行序 seed 仍可为 **20261103**（与 bootstrap 分离，写入 randomization_manifest）。  
**未改**其他统计参数。

---

## R2 S7 不可执行 — **PASS（采用方案 B）**

- 证据不足以支撑可计算方案 A（无预注册比较指标/阈值）。  
- **方案 B**：S7 **不参与自动停止**；仅诊断表（related Full 比率、hit/touch 占比 **单位=adaptive_audit 文件×步**）；禁止写成检验通过/失败。  
- S1–S6 **保持不变**。

rev3 §5.2.2。

---

## R3 Prompt/消息冻结 — **PASS**

| 项 | 实测 sha256 |
| --- | --- |
| SYSTEM_PROMPT | `4f59163597ba6982b2f77d2571792b3883198632b7cc9e8cd9ce297218dca01a`（与已知一致） |
| `build_messages` 函数源码 | `f0b477b0046282739ba1309e5035b2beb2f2f8d2564535d7154019a9aee9e436` |
| `p1_common.py`（字节读） | `e32fd30517322e8976c8f7710be69fae508c9957a926079c526f9468a3f384f2` |

构造顺序、roles、keep=24000、FILE 注入位置：**rev3 §3.1.1 已写明**。  
（注：`read_text` 编码读取整文件哈希可能与 `read_bytes` 不同，**以 bytes 为准**。）

---

## R4 字段字典 — **PASS**

rev3 §3.3.1：类型/来源/时点/缺失/指标。  
DHO/INSUFFICIENT/must/O′/Full-Digest-None/upgrade 均有行；DHO 等 **标注为导出** 非伪造原生字段。

---

## R5 错误分类矩阵 — **PASS（含待决项）**

protocol / architecture / task / infrastructure × ESR、失败率、S4、重试、记录、有效性。  
**待决**（未发明）：人工重跑策略；task 问题是否剔除（默认不剔除）。  
协议 ≠ 架构；禁止剔除失败美化 ESR。 rev3 §4.5。

---

## R6 窗口与状态 — **PASS**

- S4 窗口 = **全 run**；分子分母 = 失败 episode/尝试 episode；无新 % 阈值。  
- PASS/FAIL/NOT_TRIGGERED/NOT_APPLICABLE/INSUFFICIENT/NA 定义；NOT_TRIGGERED≠PASS；NA≠0。 rev3 §4.6、§5.2.1。

---

## 自检

| # | 项 | 结果 |
| --- | --- | --- |
| 1 | 继承 rev1→rev2→rev3 清晰 | PASS |
| 2 | R1–R6 均有结果 | PASS |
| 3 | bootstrap seed=prereg 20261102 | PASS |
| 4 | S7 非自动停止 | PASS |
| 5 | Prompt 哈希实测 | PASS |
| 6 | 字段可追溯 | PASS |
| 7 | 错误矩阵无互斥矛盾 | PASS |
| 8 | S4 全 run 窗口 | PASS |
| 9 | V13A/臂/12/R/72/安全未改 | PASS |
| 10 | 无新阈值/新调用/重试 | PASS |

## 仍存风险

- Holdout 任务尚未创建  
- DHO 等依赖导出脚本质量  
- R=2 探索性，统计功效有限  
- p1_common 整文件哈希须用 bytes（已标注）

## Git

| 项 | 值 |
| --- | --- |
| branch | `p1/v1.1` |
| HEAD | `155f934bc6c565bd304b2b7438259d592bc348c8` |
| stash | `stash@{0}` **未动** |
| 写操作 | **无** |

## 结论

| 项 | 结果 |
| --- | --- |
| R1–R6 | **全部 PASS** |
| rev3 SHA256 | **`ff070114d7388b95f3762c8221a8f297a7f2909ecc6b0dece8a1cbba2fcd355a`** |
| 建议 | **进入下一轮独立审查（M2-Revision-Fix Review）** |

**本阶段无 Holdout Freeze / 真实实验授权。**
