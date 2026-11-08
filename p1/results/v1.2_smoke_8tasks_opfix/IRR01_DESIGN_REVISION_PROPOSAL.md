# V1.2 设计修订提案：编辑目标禁止 O′（基于 IRR01 审计）

状态：**v1.2-r2.2-draft-3 · 人工原则批准；CandidateFull 语义已补齐；代码/冻结文档/测试/模型仍暂不授权**。  
本阶段不改代码/配置/任务集/冻结文档/实验结果；不跑模型。  
依据：`IRR01_EDIT_SAFETY_AUDIT.md`；V1.2-r2.1 设计与 d=2 冻结。

### 修订记录（本提案）

| 版本 | 说明 |
| --- | --- |
| draft-1 | 初稿（主方向） |
| **draft-2（本版）** | 按人工审核补齐：① excluded vs 依赖优先级 ② 保守识别边界 ③ `edit_target_full_verified` ④ 回滚开关与实验公平性；明确硬约束与 INSUFFICIENT |
| **draft-3（本版）** | 明确 **CandidateFull** 与 EditTargets 分离语义（见 §3.4）；原则批准候选定稿，待最终确认后进入文档修订 |

---

## 1. 问题摘要（事实）

IRR01 step2：

- `edit_targets` 含 **alpha.py**（真目标）；`must_full` 亦含 alpha。  
- alpha 在 step1 assistant 中有完整 FILE 且 hash 一致 → **O′ 省略** 当前 context 中的 alpha。  
- 整文件覆盖协议下，模型仅输出 `a2()` → **丢失 `a()`**。  
- 对照 D：context 全量 alpha → 成功。

**设计缺口**：r2.1 允许  
\(\mathrm{must\_full} \subseteq \mathrm{injected} \cup O'\)，  
与 **整文件覆盖编辑** 组合时，编辑目标可被“安全省略”却仍不安全。

**研究判断（人工批注）**：不得把「历史信息可复用」与「当前操作状态完整」混为一谈；本修订把该边界形式化。

---

## 2. 主修订方向

### 2.1 新不变量（硬约束，非偏好）

对每个 step \(t\)，\(EditTargets_t\) 为 **当前步、当前任务** 上由 **正向编辑意图** 解析出的目标文件集；  
\(FullInjected_t\) 为 **本轮最终发送给模型的 messages** 中，存在 **完整、可校验 FILE 内容** 的文件集合。

\[
\boxed{EditTargets_t \subseteq FullInjected_t}
\]

**必须同时满足**：

1. \(EditTargets\) 仅由 **当前任务/当前步的编辑意图** 决定（见 §3），不由“全局提及过”决定。  
2. \(FullInjected\) 以 **最终 messages** 为准（阶段 B 校验后），不是 assemble 内部集合。  
3. 历史 assistant 中的 FILE **即使 hash 一致，也不能** 代替本轮 FULL 注入。  
4. \(EditTargets_t\) **不得** 进入 O′ 省略集合。  
5. 若某 \(f\in EditTargets_t\) 无法完整注入 → **`INSUFFICIENT`**，禁止静默降级、禁止发模型请求。

非编辑目标仍遵循：

\[
f \notin EditTargets_t \Rightarrow
\begin{cases}
FULL & f\in must\_full\setminus EditTargets_t\ (\text{依赖/风险}) \\
DIGEST/NONE & \text{非 must 且臂策略允许} \\
O' & f\in Full \land O' \text{ 证明成立}
\end{cases}
\]

**不变**：整文件 `FILE:` 覆盖；不引入 diff/merge；\(d=2\)；窗口 INSUFFICIENT；E/F/G/H 非目标策略；门禁数字。

### 2.2 与 O′ 的关系

| 集合 | O′ 省略 |
| --- | --- |
| \(EditTargets_t\) | **禁止** |
| \(must\_full \setminus EditTargets_t\) | 允许（仍须最终 messages 校验） |
| 可选 Full / 非目标 | 允许（原逻辑） |

\[
O'_t \text{ 允许集 } = \{ f \mid f\notin EditTargets_t \}
\]

---

## 3. 目标识别修订

### 3.1 excluded 与依赖闭包的优先级（细节①）

**互不否定、互不改写意图：**

| 集合 | 含义 | 谁写入 |
| --- | --- | --- |
| \(EditTargets_t\) | 本轮必须写/改的对象 | 仅正向编辑子句 |
| \(Excluded_t\) | 明确禁止修改的对象 | 仅否定编辑子句 |
| \(must\_full_t\) | 必须 Full 或 O′ 证明的集合 | EditTargets ∪ risk ∪ dep/callers |

规则：

1. \(Excluded_t \cap EditTargets_t = \emptyset\)（同文件冲突见 §3.3）。  
2. \(Excluded\) **不阻止** 文件因 **依赖闭包** 进入 \(must\_full\)。  
3. 依赖进入的文件 **不因此** 变为 EditTargets（不可写回覆盖义务，除非另有正向意图）。  
4. \(f\in must\_full\setminus EditTargets\)：仍可 O′（原安全条件）。

**例**：修改 alpha；不要修改 beta；alpha 依赖 beta：

- alpha ∈ EditTargets → **必 FULL（禁 O′）**  
- beta ∉ EditTargets；可 ∈ must_full（依赖）→ **可 O′**（若证明成立）

### 3.2 保守识别的范围边界（细节②）

**禁止**“凡路径出现即 targets”。

| 提及类型 | 处理 |
| --- | --- |
| 明确编辑对象（正向编辑谓词管辖的路径/符号） | → \(EditTargets\) |
| 明确禁止修改 | → \(Excluded\)（审计） |
| 示例 / 引用 / 依赖名 / 背景 | **不自动** → EditTargets；依赖边仅影响 must_full |
| 编辑意图与路径归属不清 | **不**把全库提及都收进来；仅对 **相关候选**（如 AST 符号命中文件、依赖一步内文件、正向子句弱关联路径）保守 **FULL**，进入 **`CandidateFull`**（独立集合，**≠** EditTargets），并写 `target_resolution_reason` |

解析不清时的保守 **范围**：候选集 \(C\subseteq\)（符号命中文件 ∪ dep≤1 ∪ 指令中正向子句弱关联路径），**不是** \(\mathcal{F}_{repo}\)。

### 3.3 同文件正向 + 否定

- 同文件既有“修改 X”又有“不要修改 X” → **冲突**：保守 **进 EditTargets** + `target_resolution_reason=conflict_positive_negative`。  
- 不同文件：各归各集合。

### 3.4 CandidateFull 语义（与 EditTargets 分离）

**定义**：  
\[
CandidateFull_t \subseteq \mathcal{F}_t
\]  
为因 **目标解析不确定** 而 **保守注入完整源码** 的文件集；它 **不是** 编辑意图的证明。

| 规则 | 说明 |
| --- | --- |
| **独立集合** | \(CandidateFull_t\) 与 \(EditTargets_t\)、\(Excluded_t\)、依赖 \(must\_full\) 分开记账；**默认** \(CandidateFull_t \cap EditTargets_t = \emptyset\)（若某文件已是 EditTarget，则只记 EditTarget，不再标 Candidate） |
| **不得自动升格** | \(f\in CandidateFull_t\) **不得** 仅因被 FULL 注入就计入 \(EditTargets_t\)、edit-target ESR 分母或“真实编辑目标”统计 |
| **注入义务** | 一旦选入 CandidateFull，该文件 **必须** 实际出现在 **最终 messages** 中，且路径 + `content_sha256` 与本轮 disk 快照一致；失败 → **INSUFFICIENT**（同 EditTarget 验证强度） |
| **Kmax** | CandidateFull **不得** 被 \(K_{\max}\) 静默淘汰；与 EditTarget 一样，\(K_{\max}\) 只约束 **可选** Full（非 must、非候选、非编辑目标） |
| **O′** | CandidateFull **允许** 走 O′ 仅当 \(f\notin EditTargets_t\) 且 O′ 证明成立；若保守目的要求“本轮可见编辑基线”，实现应 **默认禁 O′**（更严）——推荐：**CandidateFull 默认禁 O′**，与“注入义务”一致 |
| **审计字段** | `candidate_full`、`edit_targets` 分列；`target_resolution_reason` 说明为何进 Candidate 而非 Target |

**避免两极端**：

1. 注入不足 → 不确定时进 CandidateFull 并强制本轮 FULL；  
2. 目标统计失真 → CandidateFull **永不** 写入 EditTargets 计数。

**例（澄清）**：

- 指令仅「实现 describe」且符号唯一命中 `mode.py` → EditTargets={mode.py}（非 Candidate）。  
- 指令仅「同步该函数」且无法归属路径 → CandidateFull={mode.py,…}；**edit_targets 仍为空或仅含已确认目标**；`edit_target_full_verified` 只对真 EditTargets 断言；Candidate 另以 `candidate_full_verified` 或并入“注入完整性”校验。

---

## 4. 运行时审计：目标识别与注入验证分离（细节③）

### 4.1 两阶段

| 阶段 | 职责 |
| --- | --- |
| 识别（plan） | 产出 `edit_targets` / `excluded` / `must_full`；**不**单独声称“已安全注入” |
| 发送前验证 | 在 **最终 messages** 上校验；失败 → INSUFFICIENT，**不请求模型** |

### 4.2 审计字段（每步，最终 messages 之后）

```json
{
  "edit_targets": ["alpha.py"],
  "candidate_full": ["mode.py"],
  "full_injected": ["alpha.py", "mode.py"],
  "edit_target_missing": [],
  "content_hash_match": {"alpha.py": true, "mode.py": true},
  "edit_target_full_verified": true,
  "candidate_full_verified": true,
  "target_resolution_reason": {"alpha.py": "positive_edit_clause", "mode.py": "ambiguous_scope_candidate_full"}
}
```

**`edit_target_full_verified = true` 当且仅当**（仅对 \(EditTargets\)）：

1. 最终 messages 中存在该路径完整 FILE；  
2. 路径规范化一致；  
3. 内容 `content_sha256` 与 **本轮装配所依据的 disk 快照** 一致。

**`candidate_full_verified`**：对 \(CandidateFull\) 同样做 1–3；失败同样 **INSUFFICIENT**。  
两者均不得用历史 assistant 省略代替本轮 FILE。

任一 \(f\in EditTargets_t\) 验证失败 →：

- `edit_target_full_verified=false`  
- `insufficient=true`，`reason=EDIT_TARGET_FULL_VERIFY_FAIL`  
- **禁止** `chat_completion`

这与既有 O′ 发送前校验并列：O′ 管“省略是否仍可见”；本字段管“编辑基线是否在本轮”。

---

## 5. 回滚开关与实验公平性（细节④）

### 5.1 开关

| 键（提案名） | 正式实验默认 | 允许关闭的场景 |
| --- | --- | --- |
| `edit_target_oprime_forbid`（或等价 `force_full_edit_targets`） | **强制 true** | 仅受控诊断 / 明确标记的 r2.1 行为复现 |
| 记录 | 每 run `run_meta` + 每步审计 | 必写开关状态 |

### 5.2 公平性

1. **同一正式实验内**，E/F/G/H **全部** 采用同一编辑目标保护规则。  
2. **禁止** E 用新规则、D 用旧规则，却声称“相同编辑安全约束下比较”。D 若作对照，须声明 D 为 v1.1 既有行为，或单独加“v1.1+edit_target_full”诊断臂（非默认）。  
3. **旧 Smoke**（`v1.2_smoke_8tasks/`、`v1.2_smoke_8tasks_opfix/`）= **历史**；修订后新 Smoke 必须 **新目录**，**禁止**与旧结果混合统计 TPSE/ESR。  
4. 编辑目标强制 FULL 会 **抬高部分任务 token** → 新旧 **绝对** token 不可严格对比；臂间相对比较在 **同一修订规则** 下仍有效。

### 5.3 Kmax

- \(K_{\max}\) 仍只约束 **可选** Full。  
- **编辑目标不受** \(K_{\max}\) 配额限制（与 must_full 不被截断一致）。

---

## 6. 文档修订范围（定稿）

| 文档 | 处理 |
| --- | --- |
| architecture | **必须**硬约束 + 不变量 + O′ 例外 |
| method formulation | **必须**数学定义（EditTargets、FullInjected、验证谓词） |
| experiment preregistration | **必须**修订记录与适用规则；**不必**改 ε/δ/门禁数字 |
| implementation roadmap | **必须**同步实施与测试 |
| novelty | 可不改（除非与边界冲突） |
| design review response | **建议**补 IRR01 缺口与本稿依据 |

预注册：新规则 **不得**伪装成原始 r2.1 内容；须以 **r2.2-draft→冻结版** 记录。

---

## 7. 实验臂与指标（不变项）

| 项目 | 处理 |
| --- | --- |
| E/F/G/H | 保留；**共同** 约束：编辑目标强制 FULL |
| d=2 | 不变 |
| Kmax | 不变；编辑目标豁免配额 |
| TPSE/TPAE | 公式不变；**重新测量** token |
| ESR 门禁 | 数字不变 |
| O′ 正确性 | **补充编辑目标例外** |

---

## 8. 测试矩阵（定稿，不实施）

| ID | 用例 | 期望 |
| --- | --- | --- |
| T-A | 编辑目标，历史 assistant 有全文 | 本轮 context 仍 FULL；不进 O′ |
| T-B | 非编辑目标 + O′ 证明 | 可省略 |
| T-C | 「不要修改 beta」 | beta ∉ EditTargets；∈ Excluded |
| T-D | 修改 alpha + 不要修改 beta | targets={alpha} |
| T-E | alpha 依赖 beta | beta 可 ∈ must；可 O′；仍 ∉ EditTargets |
| T-F | must 超窗 | 原 INSUFFICIENT |
| T-G | 最终 messages/snapshot/hash/token 一致 | 同步写盘 |
| T-H | `edit_target_full_verified` | 缺 FILE/hash 失败 → 不请求模型 |
| T-I | 回滚开关 | run_meta 可读；默认 true |
| T-J | 保守范围 | 背景提及不进 targets；不清时仅候选 FULL + reason |
| T-K | CandidateFull ≠ EditTargets | 候选注入且 verified，但 `edit_targets` 统计不含该文件；不被 Kmax 淘汰；默认不 O′ |

---

## 9. 实施风险与回滚

| 风险 | 缓解 |
| --- | --- |
| 编辑目标永不省略 → token↑ | 预期；旧 smoke 不混比 |
| 解析过宽 | §3.2 边界 + reason |
| 解析过窄 | 冲突/不清 → 保守 FULL |
| 开关误用 | 正式默认强制 on |

**回滚**：仅诊断关闭 `edit_target_oprime_forbid`；正式禁止关闭。

---

## 10. 审核状态（与人工结论对齐）

| 项 | 状态 |
| --- | --- |
| 主方向 EditTargets⊆FullInjected | **批准** |
| 四点细节（draft-2） | **已补齐并原则通过** |
| CandidateFull 语义（draft-3） | **已补齐，待最终确认** |
| 更新六份冻结设计文档 | **暂不授权** |
| 修改代码 / 单测 / dry-run / 真实 Smoke | **暂不授权** |
| P1 | **不批准** |

版本标识：**v1.2-r2.2-draft-3**。待你对 CandidateFull 语义作最终批准后，再进入六份设计文档修订。

---

## 11. 结论

1. 硬约束：\(EditTargets_t \subseteq FullInjected_t\)；历史 hash **不得** 代替本轮 FULL。  
2. excluded ⊥ 依赖 must；保守识别 **有边界**。  
3. **CandidateFull 独立**：强制本轮 FULL + 校验；**不计入** EditTargets；**不受** \(K_{\max}\) 淘汰。  
4. 运行时 **`edit_target_full_verified` / `candidate_full_verified`**；失败 **INSUFFICIENT**。  
5. 回滚开关正式默认强制；旧 Smoke 不混统计。  

等待人工最终确认 draft-3。
