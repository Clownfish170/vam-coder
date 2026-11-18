# V13E 设计：状态锚定历史（SAH · State-Anchored History）

状态：**设计稿 v1（未冻结）**
日期：2026-11-10
基座：F（v12F）与 ICG（v13c）**双基座**；组件 **S1 + S2 全做**；第一轮 **1.5B 筛选**
铁律：不改 VSO/O′/pre_send 语义，不改任务集，不改 ESR 口径

---

## 0. 一句话

> 历史从「assistant 输出全文转写」改为**工作区状态投影**（每文件只留最后一版）+
> **义务账本**（历史指令常驻一行）；投影对 O′ 校验**可证明等价**，账本补上「要求蒸发」这一真实失效模式。

---

## 1. 诊断依据（DS 504 集，逐题对齐）

| 事实 | 数字 | 出处 |
| --- | --- | --- |
| ICG vs F 的 ESR 差 | −1.2pp（0.613 vs 0.625），逐题 5 掉 3 涨 48 平 | `analysis_report.md` §1/§3 |
| 失败形式 | 失败集 61/65 末步写 FILE 仍不过；NO_EDIT 仅 4 | `episodes/**/steps/stepN/response.txt` |
| 改写丢内容率 | F 6% · CR 6% · ICG 4%（无架构特异签名） | 末版 < 75% 最长版代理 |
| ICG 旋钮几乎不发作 | 312 个 ICG 步：`icg_skipped` 共 **1** 次、`icg_selected≥1` 共 27 步、15/56 题动过 | `injection_audit.jsonl` |
| related 通道总价值 | F−CR = **44 tok/集**；C−A = −55 tok，CI 含 0 | `analysis_report.md` §2 |
| 历史占比 | 末步 prompt 历史占 **63%**；全量累计 prompt 历史占 **~45%**（870K/1.9M tok） | 504 集 messages 重放 |
| 历史构成缺陷 | **历史 user 指令全部丢弃**，eval 结果不进 messages | `run_p1_v12.py:476`（只 append assistant） |
| 典型失效 | L06a ICG 0/3：step3 指令「codec.py 加 encode2/decode2」漏做后再无人提醒，终步源码无 encode2 → NO_EDIT | `episodes/ind_L06a/**` |

**结论**：ICG 的 ESR 差在噪声内、无系统性失败签名；收益小的根因是**杠杆空**（related 通道只值 ~44 tok）。
要「补差距 + 扩收益 + 扩创新」，必须把杠杆换到**历史构成**上。

DS 四臂锚点（同 56 题，168 集/臂，memory_off 补跑已完成）：

| 臂 | ESR | prompt/集 |
| --- | ---: | ---: |
| memory_off | 0.613 | 4265 |
| v12_F | 0.625 | 3800 |
| v13A_CR | 0.649 | 3756 |
| v13B_ICG | 0.613 | 3745 |

---

## 2. 机制

### S1 状态投影（`sah_project`）

对进入 messages 的历史做**逐块 last-write-wins**：

1. 只处理 **assistant** 消息中的 `FILE: path\n``` … ``` ` 块；system / user / 非 FILE 消息原样保留。
2. 按归一化路径统计每个块的**最后一次出现**；被更晚出现覆盖的块，正文替换为一行折叠标记
   （形如 `（历史折叠）path 的较早版本已省略，仅保留其最新版本。`）。
3. 折叠标记**不得**匹配 `_ASSIST_FILE_RE`（不以 `FILE:` 开头、无围栏）→ 不参与哈希提取。

一条消息含多块时逐块判定；只删「被覆盖的块」，消息结构不变。

### S2 义务账本（`sah_ledger`）

当前 harness 逐步**只 append assistant 输出**，历史指令与 eval 反馈全部不进 messages。
S2 在 user 消息中 TASK 与 CONTEXT 之间插入：

```text
=== TASK ===
<本步指令>

=== OBLIGATIONS ===
- [3] <step3 指令全文（上限 200 字）>
- [4] <step4 指令全文>

=== CONTEXT ===
…
```

- 仅存**历史**指令（不含本步），本步仍在 TASK。
- 账本只含指令文本，**不含任何文件正文**；不产生 `FILE:` 围栏。
- memory_off 锚臂**不开** S1/S2（锚定义不变）。

---

## 3. O′ / VSO 等价性（可证明 + 可单测）

阶段 A `tracker_from_history`（`proof.py:10-21`）与阶段 B `verify_omissions_in_messages`
（`messages_visibility.py:69-136`）提取历史文件的方式**是同一个函数**
`full_files_in_messages`（`messages_visibility.py:27-42`），其语义为**按路径后写覆盖的 dict**。

因此：删掉「非最后一次出现」的块，对 `full_files_in_messages(H)` **零影响** ⇒

- 阶段 A 候选证明不变 → O′ 省略判定不变 → assemble 输出不变；
- 阶段 B 校验池不变 → `PreSendCheck` 结果**逐字段相等**；
- E/C 完整性只看**当前 CONTEXT**（`current_context_files`），与历史无关。

**测试断言**：对合成历史 + DS 504 集真实历史重放，
`full_files_in_messages(project(H)) == full_files_in_messages(H)` 且
`verify_omissions_in_messages` 的 `ok / missing_or_mismatch / reasons` 全等。

注入点：`run_p1_v12.py:242` trim/redact 之后、`hist_est`/`proof_tr`/`build_messages` 之前
（三者都用同一份投影后历史，避免证明与实发不一致）。

---

## 4. 成本预算（DS 504 集 / 2808 步真实 messages 重放，实测）

重放脚本：`p1/experiments/v13e_sah/verify_projection.py` → `replay_report.json`

| 项 | 累计 chars | 占比 | 估 tok/集 |
| --- | ---: | ---: | ---: |
| baseline（原样 messages） | 6,610,566 | — | 3279 |
| **S1 投影后** | 4,812,996 | **−27.19%** | **−891** |
| **S1 + S2 账本** | 5,545,029 | **−16.12%** | **−528** |

- 账本按**上界**计（每步都含全部历史步指令、不截断）：+163 tok/集。
- 对照现状 CR/ICG 的 −55 tok（CI 含 0）：**效应量约 10 倍**；对 F 的 3800 API prompt ≈ **−14%**。
- **等价性硬断言：504 集 0 失败** —— 逐字段比对 `full_files_in_messages` 与
  `verify_omissions_in_messages`（ok / missing_or_mismatch / reasons / visible_hashes /
  et·cf 完整性），disk_sha 取实盘、省略与 E/C 清单取各步 `pre_send_check.json`。
- `max_history_chars=24000` 实测从未触发（历史峰值 5,737 chars），投影不受其影响。

---

## 5. 臂定义（不改既有臂）

| 臂键 | 架构 ID | 配置差异（相对基座） |
| --- | --- | --- |
| `V13EPROJ` | `vam_coder_v1.3E_PROJ` | F + `sah_project`（S1 消融） |
| `V13ESAH` | `vam_coder_v1.3E_SAH` | F + `sah_project` + `sah_ledger`（**主臂**） |
| `V13ICGSAH` | `vam_coder_v1.3E_ICGSAH` | ICG + `sah_project` + `sah_ledger`（全栈） |

`AblationConfig` 新增两个布尔字段，默认 `False` → 既有四臂配置摘要与冻结快照**逐字节不变**。

---

## 6. 实验计划（与 P1 锚点对齐）

1. **离线（零模型调用）**：504 集真实历史重放 → 等价性断言 + 精确收益表。
2. **1.5B 筛选**：testpart 8 题 × 3 rep，臂 =
   `memory_off`（锚，已有）· `F`（已有）· `ICG`（已有）· `V13EPROJ` · `V13ESAH` · `V13ICGSAH`（新跑 3 臂）。
   - 安全：INSUFFICIENT=0、DHO=0、ET/候选仍当前 CONTEXT 全文、等价性断言通过
   - 能力：ESR ≥ F − 0.10 且 ≥ ICG − 0.10（非劣）
   - 效率：`V13ESAH` 集总 prompt ≤ F，且相对 F 的降幅 ≥ 8%（低于此说明投影未生效）
   - 机制：`history_file_blocks` 下降、`sah_folded>0`、账本行数 = 步数−1
3. **过门 → DS 预注册**：新批 56 题 × 3 rep，主比较 `V13ESAH−F`、`V13ICGSAH−ICG`；
   锚 memory_off/F/ICG 沿用同题重跑或按预注册声明复用规则（**冻结后再发确认性请求**）。

---

## 7. 创新表述与文献边界

**可写：**

1. **Memory as state, not transcript**：历史不是模型输出回放，而是工作区状态投影——信息论上对
   「当前状态」无损，且**消除与磁盘矛盾的陈旧快照**（观测到的失效诱因之一）。
2. **Proof-preserving projection**：投影与 O′ 的「按路径后写覆盖」语义**同构**，故省略授权与
   发送前校验可证明不变——把安全证明写进记忆压缩，而非事后补检。
3. **Obligation ledger**：记忆同时保存「我做过什么」与「还欠什么」；指令不再随历史蒸发（零 LLM、确定性）。
4. 组合协议与 P1/非劣口径一致，单独消融 S1 / S2。

**不能写：** 通用长期记忆、LLM 反思/摘要压缩（我们零 LLM）、比 MemGPT/Voyager「记忆更强」的无对照断言、未做同仓多任务的跨集大幅省 token。

---

## 8. 风险与止损

| 风险 | 止损 |
| --- | --- |
| 删旧快照降低 ESR（模型需看「我改过什么」） | 账本 + 最新版仍在；1.5B 上 S1 消融臂 `V13EPROJ` 单独判；ESR 掉 >10pp 即弃 S1 保 S2 |
| 账本引入干扰/让模型重复编辑 | 账本仅指令文本、无状态断言；1.5B 观察 `sah_ledger` 臂 NO_EDIT 与重复编辑率 |
| 折叠标记被误解析为 FILE 块 | 单测：投影后 `full_files_in_messages` 键集不变、标记不匹配正则 |
| 与 trim/redact 顺序冲突 | 固定顺序 trim → redact → project；redact 模式下投影只作用于仍匹配的块 |
| 收益不及预期 | 离线脚本先出**精确**（非估算）收益表，达不到 −8% 直接停，不烧 1.5B |

---

## 9. 落点

| 模块 | 职责 |
| --- | --- |
| `p1/scripts/v12/history_project.py` | `project_history()`（S1，纯函数） |
| `p1/scripts/p1_common.py` | `build_messages(..., ledger_lines=None)`（S2，可选参数） |
| `p1/scripts/v12/config.py` | `sah_project` / `sah_ledger` 字段 + 3 个臂 |
| `p1/scripts/run_p1_v12.py` | V12_ARMS 映射；trim 后投影；指令日志；三处 build_messages 传账本 |
| `p1/tests/test_v13e_sah.py` | 等价性、标记不误匹配、账本结构、默认关闭回归 |
| `p1/experiments/v13e_sah/verify_projection.py` | 504 集重放：等价性 + 精确收益 |

**VSO / messages_visibility / assemble 语义：零修改。**
