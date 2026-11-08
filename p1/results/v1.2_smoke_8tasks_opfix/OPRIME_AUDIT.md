# V1.2 O′ 修复后真实模型 Smoke — O′ 专项审计报告

输出目录：`p1/results/v1.2_smoke_8tasks_opfix/`  
配置：8 任务 × E/F/G/H × R=1 + D(v1.1) 参照；d=2；Q6_K 1.5B；API 错误 0。  
旧目录 `v1.2_smoke_8tasks/` **未覆盖**。

---

## 1. 发送前强制校验（运行时）

| 检查 | 结果 |
| --- | --- |
| 每步存在 `pre_send_check.json` | **64/64** |
| 运行时 `pre_send.ok` | **全部 True** |
| `revised`（阶段 B 回退） | **0** 次（阶段 A 历史证明已足够，无需回退） |
| `INSUFFICIENT` | **0** |

解释：修复后阶段 A 仅用 trim 后历史证明；多数 omit 发生在 step2，且 step1 assistant 已 FILE 回写 → 省略在发送时合法，无需 force_full。

---

## 2. 最终 messages 完整性（对每个 omit 文件）

| 检查 | 结果 |
| --- | --- |
| 省略文件出现在最终 `messages.json` 的完整 FILE 中 | **全部 True**（`in_messages=True`） |
| 不存在“省略且 messages 中无源码” | **是（修复成功的核心标准）** |

### 与“发送后 workspace”的哈希

对 **run 结束后** 的 workspace 再比哈希时，部分 step2 被省略文件出现 `hash_mismatch`——原因是 **step2 模型 apply 后磁盘已变**（如 invoice/app/alpha/bill），**不是**发送时校验失败。

发送时：`pre_send.ok=True`（对照当时 disk_sha）。  
事后 workspace 哈希 **不能** 作为发送时 O′ 失败证据。

分类汇总：

| 类型 | 数量 |
| --- | --- |
| omit ∩ 最终 messages 含全文 | **全部 omit 事件** |
| omit ∩ 发送时 pre_send 失败 | **0** |
| 事后 disk 哈希漂移（模型已编辑） | 若干 step2 文件（预期） |

---

## 3. force_full 与最终 prompt

| 检查 | 结果 |
| --- | --- |
| force_full 非空的步骤 | **0** |
| force_full 仍出现在 omitted | **0**（无此案例） |
| CFD01 / E / step2 | omit=`[tax.py]`；context 含 **invoice.py FULL**；messages 中 tax 为 assistant FILE 且 hash 当时一致 |

---

## 4. pre_send_check ↔ messages.json

- 每步 `messages.json` 在 verify 之后写入；`chat_completion` 使用同一 list。  
- `prompt_hashes.csv` 64 条，sha256 全唯一。  
- 未发现 snapshot 与发送对象分叉的证据。

---

## 5. hash_match_all（发送时口径）

- 运行时 `verify_omissions_in_messages`：全部 omit 事件 **ok=True**。  
- **发送时 hash_match_all = PASS**。  
- 事后 workspace 对比：仅“模型已改文件”出现漂移（见 §2）。

---

## 6. 与修复前 Smoke 对比（描述性，非统计）

| | 修复前 | 修复后 |
| --- | --- | --- |
| E ESR | 1/8 | **3/8** |
| F/G/H ESR | 1–2/8 | 1–2/8 |
| D ESR | 4/8 | 4/8 |
| NO_EDIT（E/F/G/H） | 25 | **16** |
| 消息中 omit 无源码 | CFD01 等存在 | **未发现** |

仍 **不能** 宣称优于 memory_off 或统计显著。

---

## 7. 结论

| 项 | 判定 |
| --- | --- |
| O′ 最终 messages 不变量 | **PASS** |
| 无“盲区省略” | **PASS** |
| 阶段 B 闭环可用 | **PASS**（本 Smoke 未触发 revise，路径已单测+代码审查） |
| 总体 O′ 修复验收 | **PASS WITH WARNINGS**（WARN：事后 workspace 哈希不可用于事后 O′ 判分；空文件/路径大小写风险仍在） |

**建议可进入你的下一步审核**；本报告不授权 P1。
