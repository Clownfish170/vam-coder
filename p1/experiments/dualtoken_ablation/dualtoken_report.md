# 双 Token 专项实验报告（dualtoken_ablation）

日期：2026-11-07 · 状态：**完成**（960/960 全 OK，0 失败，累计 3,308,934 tokens，S5=8M 内）
冻结依据：补记 `v12f_validation_preregistration_addendum_dualtoken.md`（sha `d664d602…`）
分析脚本：`analyze_dualtoken.py`（bootstrap seed=20261102 / B=10000 / cluster=task_id；sign-flip B=10000；非劣 margin −12pp；Holm 于 B−D、C−D）
数据：`episode_metrics.csv`、`metrics_summary.csv`、`bootstrap_results.csv`、`signflip_tests.csv`、`cire_summary.csv`、`dualtoken_analysis_manifest.json`

---

## 1. 判定总表（按补记 §4 冻结假设）

| 假设 | 主判定 | 依据（冻结口径） |
| --- | --- | --- |
| **H-B**（B 相对 D：prompt↓ 且 ESR 非劣） | **不支持** | prompt B−D = **−28.7 tok/集**（95% CI [−57.8, −4.2]，bootstrap 排除 0）但 sign-flip Holm p=**0.109 > 0.05**；ESR 配对差 CI 下界 **−14.6pp < −12pp** → 非劣**未通过** |
| **H-C**（C 相对 D：同上） | **不支持** | prompt C−D = **−29.0**（CI [−57.9, −4.7]）Holm p=**0.109**；ESR CI 下界 **−15.0pp < −12pp** → 非劣**未通过** |
| **H-AB**（C−B 分离静态表示与寻址贡献） | **不支持** | C−B prompt = **−0.3 tok**（CI [−5.6, +5.9] 含 0）→ 两成分**不可分离**（几乎同价） |
| （补记次级）A 相对 D 的 O′/选择性交付收益 | **方向支持**（次级，非双 Token 主张） | A−D prompt = **+403.1 tok/集**（A 更高），task 级 sign-flip p=0.0001；ESR 0.925 vs 0.917（n.s.） |

**结论（与任务书立场一致）**：双 Token（符号寻址 / 静态表示+符号 ID）的**独立贡献仍未被证实**——prompt 降幅小（~1.1%）且未过 Holm，ESR 非劣在冻结口径下失败，两成分不可分离。**论文不得主张双 Token 独立收益**；A−D 的收益属于 O′/选择性交付机制（与 P2 消融 O′=−398 tok 相互印证），不得归因双 Token。

## 2. 各臂总体指标（240 集/臂；同模型同 tokenizer，组间可比）

| 臂 | ESR | prompt/集 | peak context | growth (tok/step) | RTR | 寻址开销 (tok/集) | CMR_context | CMR_visible(次) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A inline_full（无 O′ 基线） | 0.9250 | **2907.7** | 638.3 | 69.6 | **0.342** | 0 | **0.705** | 0.892 |
| B symbolic_addressing | 0.8542 | 2475.9 | 538.6 | 74.2 | **0.170** | 3.3 | 0.572 | 0.889 |
| C static+symbolic_id | 0.8458 | 2475.6 | 538.5 | 74.2 | 0.171 | 4.3 | 0.573 | 0.893 |
| **D vam_coder_v1.2_F（参照）** | 0.9167 | 2504.5 | 544.1 | **56.1** | 0.187 | 0 | 0.572 | 0.891 |

读法：
- **A 最贵最全**（内联全量、无 O′）：RTR 最高（0.342，跨步重发最多）、CMR_context 最高——符合"内联上界"定位。
- **B/C 相对 D 只省 ~29 tok/集**（相关非目标块换成符号/静态行的净效果），RTR 略降（0.187→0.170）；寻址开销本身极小（3–4 tok/集）。
- **A−D ≈ 403 tok/集** 即 O′+选择性交付的收益，量级与 P2 的 O′=−398 tok 一致（相互印证）。
- CMR_context：B/C 与 D 几乎相同（0.572）——预声明信息点多位于 must/闭包/编辑目标文件（不变换区）或指令内，符号化未直接抹掉它们；A 更高源于全量内联。
- CMR_visible（含指令+历史，次级口径）四臂均 ~0.89——可见面送达率对表示方式不敏感。

### 难度分层（ESR / prompt）

| 臂 | short ESR | medium ESR | long ESR | short prompt | medium prompt | long prompt |
| --- | --- | --- | --- | --- | --- | --- |
| A | 0.8125 | 1.0000 | 0.9625 | 622.8 | 1971.2 | 6129.1 |
| B | **0.5875** | 1.0000 | 0.9750 | 533.4 | 1787.5 | 5106.7 |
| C | **0.5875** | 1.0000 | 0.9500 | 533.8 | 1783.8 | 5109.1 |
| D | 0.7875 | 1.0000 | 0.9625 | 623.3 | 1792.4 | 5097.9 |

ESR 差距**全部集中在 short 层**（B/C 0.5875 vs D 0.7875）；medium/long 四臂相当。

## 3. 失败归因（关键披露）

B/C short 层 33 集失败（每臂）分解：

1. **~20 集/臂（全部难度）= INSUFFICIENT 跳发**：pre_send 安全门报 `EDIT_TARGET_FULL_VERIFY_FAIL`（例：`p1_S02b` step1：engine.py 可见哈希 ≠ 磁盘哈希 → `ok:false` → **不发模型请求**、eval 记失败）。transform 设计上不改动编辑目标（ET）块，但最终 messages 的 ET 完整性校验未通过——属 **B/C 实现与安全门的交互问题**（实验代码，非生产代码；run_meta `production_code_modified=false`）。
   - 安全门行为本身是**正确的 fail-closed**（拒绝发送不一致上下文），代价按冻结口径记入 ESR。
2. **剩余失败 = 真实模型失败**：集中在 b/c 变体（如 `p1_S02b` step2 写出错误常量应用），与表示噪声对短任务的干扰一致（机制解释，非预注册主张）。

**敏感性（探索性披露，不改主判定）**：排除 INSUFFICIENT 跳发集后——

| 臂 | gross ESR | clean ESR（排除跳发） |
| --- | --- | --- |
| A | 0.9250 | 0.9250（n=240，无跳发） |
| B | 0.8542 | **0.9318**（n=220） |
| C | 0.8458 | 0.9227（n=220） |
| D | 0.9167 | 0.9167（n=240） |
| B/C short 层 | 0.5875 | **0.7833**（n=60）≈ D 的 0.7875 |

即：**非劣失败由安全门跳发驱动，而非模型能力下降**；排除后 B/C 与 D 相当。主判定（不支持）不变——冻结数据不改、口径不换；该归因为未来若修复 B/C 实现后重检提供明确方向。

## 4. 专项指标（补记 §5）

- **Peak Context**：A 638 > D 544 ≈ B/C 539（tok/集均值）。
- **Context Growth Rate**（episode 内 OLS 斜率均值）：D 56.1 最低；A 69.6；B/C 74.2——描述性（任务难度混合影响斜率，不作主张）。
- **Redundant Token Ratio**（同 sha 文件块跨步重发占比，chars 比值≈token 比值，披露）：A 0.342 **最高** > D 0.187 > C 0.171 ≈ B 0.170 **最低**——与补记预测方向（A 最高、B 最低）一致。
- **Retrieval Overhead**（`--- SYMBOL/SYMBOL_SOURCE/STATIC` 标记块 chars/4）：B 3.3、C 4.3 tok/集；C>B（静态行略长于符号行），A/D=0。
- **Latency**（t_model_ms/t_step_ms 汇总于 episode_metrics.csv）：与 token 量同向，无异常热点。

## 5. 统计明细（主比较）

| 比较 | 指标 | 点估计 | 95% CI | sign-flip p | Holm p（主） |
| --- | --- | --- | --- | --- | --- |
| B−D | prompt/集 | −28.65 | [−57.75, −4.25] | 0.0567 | 0.1090 |
| B−D | ESR | −0.0625 | [−0.1458, +0.0083] | 0.1622 | 0.1858 |
| C−D | prompt/集 | −28.96 | [−57.86, −4.66] | 0.0545 | 0.1090 |
| C−D | ESR | −0.0708 | [−0.1500, 0.0000] | 0.0929 | 0.1858 |
| A−D（次级） | prompt/集 | +403.1 | （见 signflip_tests.csv） | 0.0001 | NA |
| C−B（H-AB） | prompt/集 | −0.30 | [−5.56, +5.88] | 0.9228 | NA |

## 6. 方法与边界披露

1. 四组同模型（deepseek-v4.1-flash-1017）同 tokenizer，组间可比；**不跨模型合并**。
2. RTR/寻址开销按 chars/4 估计为 token（与运行 config `chars_per_token=4` 一致），比值型指标不受单位影响。
3. CMR 沿用 CIRE 口径（144 个 P1 预声明信息点；context 主口径 + visible 次口径）；point_steps=1500/臂。
4. 非劣判定用冻结主口径（含跳发失败）；敏感性口径明确标注探索性。
5. 本实验为**确认性机制专项**（补记假设预注册在先）；任何事后解读（如 short 层机制）标注为解释性。
6. **红线**：不主张双 Token 独立收益；不把 A−D 收益归因双 Token；不把本报告结果与 Part4 独立集结果混并。

## 7. 对总任务书的落点

- RQ5 证据矩阵（待总报告 §7.3 填）：双 Token 行 = **独立贡献未证实**（专项数据支持该立场）。
- 论文 Method 中双 Token 仅作实现细节描述，不进贡献列表（与总报告 §9.13 红线一致）。
- 遗留（可选后续，非本任务书必需）：修复 B/C 的 ET 可见哈希一致性后按同冻结口径重检 H-B/H-C（需新补记，不在本冻结内）。
