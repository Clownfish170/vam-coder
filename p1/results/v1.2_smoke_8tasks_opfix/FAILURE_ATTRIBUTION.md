# V1.2 Smoke（O′ 修复后）失败归因审计（只读）

数据：`p1/results/v1.2_smoke_8tasks_opfix/`  
范围：8 任务 × E/F/G/H + D(v1.1)；R=1；**不改代码、不跑模型**。  
明细表：`failure_attribution_steps.csv`

---

## 1. 步级类别汇总

| 类别 | E | F | G | H | D |
| --- | --- | --- | --- | --- | --- |
| EDIT_APPLIED_EVAL_PASS | 8 | 6 | 7 | 7 | 9 |
| EDIT_APPLIED_BUT_EVAL_FAIL | 4 | 6 | 5 | 5 | 3 |
| NO_EDIT | **4** | 4 | 4 | 4 | **4** |
| NOTE_INS_VIOL / 协议其他 | **0** | 0 | 0 | 0 | 0 |
| 空响应 / 模型错误 | 0 | 0 | 0 | 0 | 0 |

**结论（事实）**：本轮失败 **无** NOTE_INS_VIOL；主形态是 **NO_EDIT** 与 **已落盘但 eval 失败**。  
无“FILE 解析失败但响应非空”（rejected=[]）。

---

## 2. Episode 成功对照

| 臂 | 成功任务 |
| --- | --- |
| D | CFD01, DEL01, IRR01, RFS01（**4/8**） |
| E | CFD01, DEL01, RFS01（**3/8**） |
| F | 仅 CFD01（1/8） |
| G/H | CFD01, RFS01（2/8） |

---

## 3. E vs D 逐任务配对

| 任务 | E | D | 配对 |
| --- | --- | --- | --- |
| v1_CFD01 | 1 | 1 | both_success |
| v1_DEL01 | 1 | 1 | both_success |
| v1_RFS01 | 1 | 1 | both_success |
| **v1_IRR01** | **0** | **1** | **D_only_success** |
| v1_RUR02 | 0 | 0 | both_fail |
| v1_RUR03 | 0 | 0 | both_fail |
| v1_DUP01 | 0 | 0 | both_fail |
| v1_STM02 | 0 | 0 | both_fail |

- **E 成功且 D 失败**：无  
- **D 成功且 E 失败**：仅 **IRR01**  
- 其余失败为 **双方同败**（协议/推理为主，与臂无关）

汇总 3/8 vs 4/8 的差距 **全部来自 IRR01**。

---

## 4. 按原因归类（带证据）

### 4.1 NO_EDIT（模型未输出修改）

**事实**：响应体恰为 `NO_EDIT`，`applied=[]`，eval 失败。

| 臂 | 任务 | 上下文（E） | 归因 |
| --- | --- | --- | --- |
| E–H | RUR02 s1 | hot FULL + stable INDEX | **模型违例**（hot 在上下文中仍 NO_EDIT） |
| E–H | RUR02 s2 | hot FULL（或省略后视臂而定） | 模型违例 |
| E–H | RUR03 s1 | core FULL | 模型违例 |
| E–H | DUP01 s1 | mathx+textx FULL | 模型违例 |

D 同任务同样 NO_EDIT（RUR02/03 s1，DUP01 s1）→ **与 V1.2 装配无关的 1.5B 协议问题**。

### 4.2 输出协议违规

- **未发现** NOTE_INS_VIOL 或非 FILE/NO_TEXT 异常协议。  
- FILE 块均成功 apply（rejected 空）。

### 4.3 上下文不足 / O′ 相关

**发送时 O′**：全部 omit 的 `pre_send.ok=True`，最终 messages 含全文（见 OPRIME_AUDIT）→ **无发送时盲区**。

**但存在“省略后模型写不完整文件”**（O′ 的下游风险）：

| 任务 | 现象 | 机制 |
| --- | --- | --- |
| **IRR01 E s2** | 上下文仅有 `beta.py`；`alpha.py` 被 O′ 省略（s1 assistant 已回写 alpha）。模型输出 **仅** `a2()`，覆盖后丢失 `a()` → `NameError` | 省略后模型 **重写文件** 时未合并历史中的完整 alpha |
| **STM02 E s2** | bill/fee 均 omit；模型仍写出 due_fast 但算错（12≠13） | 更偏推理；上下文依赖历史完整源码 |
| **CFD01 E s2** | 仅 omit tax；invoice 仍在 context → **成功** | 单文件 omit 且目标明确时可接受 |

**事实 vs 推测**：

- **F**：IRR01 s2 context 无 alpha FULL；模型 FILE 只含 a2；eval NameError。  
- **H**：若 s2 仍注入 alpha FULL，模型更可能写出完整文件（D 即如此：完整 alpha+a2）→ **O′ 省略是 IRR01 从 D 成功变为 E 失败的充分解释路径**。

### 4.4 任务执行 / 推理错误（已落盘仍失败）

| 任务 | 现象 | 归因 |
| --- | --- | --- |
| RUR03 s2 | 改了 core 但 c3 断言失败 | **模型推理** |
| DUP01 s2 | 写了 norm/norm2 仍失败 | **模型推理/协议细节** |
| STM02 s2 | due_fast=12≠13 | **模型推理**（与 V1.1 正式诊断同型） |
| IRR01 E s2 | 不完整重写 | **O′ 下游 + 模型写全文件能力** |

### 4.5 Digest 内容不足

- 仅 E 在 RUR02 s1 使用 INDEX（stable_*）。  
- RUR02 仍 NO_EDIT → **无证据**表明 Digest 单独导致失败；主因仍是模型不编辑 hot。

---

## 5. 逐失败步归因（E）

| 任务/步 | 类 | 主因 | 次因 |
| --- | --- | --- | --- |
| RUR02 s1 | NO_EDIT | 模型协议 | Digest 非主因 |
| RUR02 s2 | NO_EDIT | 模型协议 | |
| RUR03 s1 | NO_EDIT | 模型协议 | |
| RUR03 s2 | 已应用失败 | 推理 | |
| DUP01 s1 | NO_EDIT | 模型协议 | |
| DUP01 s2 | 已应用失败 | 推理 | |
| STM02 s2 | 已应用失败 | 推理 | O′ 省略 bill/fee（非充分因） |
| IRR01 s2 | 已应用失败 | **O′ 省略致不完整重写** | 模型未从历史拼全文件 |

---

## 6. 总判断

1. **协议违规（NOTE_INS_VIOL）**：本轮 **0**。  
2. **NO_EDIT**：RUR02/03/DUP01 双方同败 → **模型能力/任务难度**，不是 V1.2 独有。  
3. **E vs D 唯一分歧 IRR01**：可归因到 **O′ 省略 alpha + 模型不完整重写**（D 全源注入则成功）。  
4. **发送时 O′ 安全**：仍成立；风险转移到 **“省略后编辑历史中文件”** 的模型行为。  
5. 汇总 3/8 vs 4/8 **不宜**解读为架构全面劣势；**也不宜**忽略 IRR01 暴露的省略编辑风险。

---

## 7. 建议（诊断层，非改码授权）

若后续要改设计（另授权）：

1. **编辑目标相关文件禁止 O′**（IRR01 中 alpha 是编辑目标却在 s2 被省略——需核对 must 规则：s2 目标若仅点名 a2 而未点名 alpha 文件）。  
2. 或：省略时强制附带 **签名/函数列表** 而非完全不见。  
3. 保持 RUR 类 NO_EDIT 为模型边界，不归咎记忆层。

**本阶段：只读归因完成；未改代码、未跑模型。**
