# V1.2-r2.2 文档修订计划（草案）

状态：**计划稿 · 未获文档修订授权**。  
依据：`IRR01_DESIGN_REVISION_PROPOSAL.md` draft-3（人工已批 CandidateFull 语义）；  
**禁止**在明确授权前修改六份冻结设计文档或代码。

---

## 0. 集合关系（定稿语义，写入 method/architecture）

设 step \(t\)：

| 符号 | 集合 |
| --- | --- |
| \(E_t\) | EditTargets（真实编辑目标） |
| \(C_t\) | CandidateFull（保守候选） |
| \(M_t\) | must_full（编辑目标 ∪ 依赖/风险 ∪ 必须 Full） |
| \(F_t\) | FullInjected（最终 messages 中完整注入的文件） |

**约束**：

\[
\begin{aligned}
E_t \cap C_t &= \varnothing \\
E_t \cup C_t &\subseteq F_t \\
E_t &\subseteq M_t
\end{aligned}
\]

- \(E_t \subseteq M_t\)：编辑目标 **必须** 进入 must_full。  
- \(M_t\) 还可含非编辑目标（依赖、risk）。  
- \(C_t \subseteq F_t\)：候选必 FULL 注入；**不受** \(K_{\max}\) 淘汰；验证失败 → INSUFFICIENT。  
- \(E_t \subseteq F_t\)：硬约束；**禁止**用历史 assistant 省略代替本轮 FULL。  
- O′ 允许集：\(f \notin E_t \cup C_t\)（**Candidate 默认禁 O′**）。

审计：`edit_target_full_verified` 与 `candidate_full_verified` **分列**，禁止合并为单一 `full_verified`。

---

## 1. 授权边界（本计划执行前提）

| 项 | 状态 |
| --- | --- |
| draft-3 CandidateFull | **已批准** |
| 本修订计划 | **待你审核授权** |
| 改六份冻结文档 | **未授权** |
| 改代码/测试/配置/跑模型 | **未授权** |
| P1 | **不批准** |

---

## 2. 六份文档修订矩阵（授权后执行）

| 文档 | 动作 | 写入要点 |
| --- | --- | --- |
| `v1.2_architecture_design.md` | **必须改** | §3.4.1 正向/否定解析；EditTargets ⊆ must ⊆ 意义澄清；O′ 禁 EditTarget/Candidate；\(E\subseteq F\)；T 规则；版本 r2.2 |
| `v1.2_method_formulation.md` | **必须改** | §2 解析；§3 \(E,C,M,F\) 与三条集合约束；ok(s) 对 E/C 用 CurrentContext；验证谓词；Kmax 豁免 E/C |
| `v1.2_experiment_preregistration.md` | **必须改** | 修订记录 r2.2；适用规则（全臂共同编辑目标保护）；**不改** ε/δ/门禁数字/d=2；声明与 r2.1 行为差异 |
| `v1.2_implementation_roadmap.md` | **必须改** | targets 意图解析、CandidateFull、force_full、双 verified 字段、开关默认 on、测试 T-A–T-K |
| `v1.2_novelty_and_related_work.md` | 默认 **不改** | 仅当表述与“历史≠当前操作状态”边界冲突时加一句 |
| `v1.2_design_review_response.md` | **建议改** | 追加 IRR01 缺口 → r2.2 修复依据（只读摘要，不重写历史） |

可另增：`p1/docs/v1.2_r2.2_change_note.md`（一页变更说明，便于 diff 审查）——**待你指定是否新建**。

---

## 3. 修订顺序（授权后）

1. method（数学与验证谓词）  
2. architecture（规则表与不变量）  
3. prereg（版本行 + 适用规则，门禁数字不动）  
4. roadmap（实施/测试）  
5. design_review_response 补记（可选）  
6. 哈希快照 + `git status` 只读核验（仍不 commit）

---

## 4. 明确不改的内容

- E/F/G/H 臂 ID 与非目标策略表  
- d=2、Kmax 数值、ESR/TPSE/TPAE 门禁、bootstrap seed  
- 整文件 FILE 协议  
- P0/v1.0/v1.1 资产、tasks、manifest、formal_runs  
- 代码与测试（另阶段）

---

## 5. 审核检查单（改完后给你）

- [ ] 三套集合关系与独立 verified 字段写入 method+arch  
- [ ] prereg 含 r2.2 修订记录且门禁数字未变  
- [ ] 与 draft-3 无矛盾  
- [ ] 六份 SHA 变更清单  
- [ ] 冻结资产 SHA 未变  

---

## 6. 结论

计划就绪。**等待你授权“修改六份冻结文档”后**，再执行 §2–§3；在此之前 **零改动** 冻结文档与代码。
