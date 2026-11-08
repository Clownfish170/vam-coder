# VP / INSUFFICIENT 运行时门禁报告

正式名称：**Visibility Proof for Safe Omission（VP / vproof）**。  
O′ 仅历史追溯。

**性质：Mock/单集测试 + 代码审查。不是真实模型 P1。**

---

## 1. 代码路径（run_p1_v12.py）

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| `should_call_model` 定义 | 有 | 约 L78 |
| 门闩调用行 | **L316** `allow_model, block_reason = should_call_model(...)` | 实测 |
| 唯一 `chat_completion(` | **L326**（cr = …） | 实测仅 1 处 |
| gate 在 chat 之前 | **True** | 316 < 326 |
| 其他 v12 调用路径/retry | **无** | grep 单点 |
| dry_run 与真实同一 allow_model | **是** | L317–325 |
| pre_send/messages 在发送前写盘 | **是** | L273–291 写盘在 L316 前 |
| INSUFFICIENT 后继续 chat | **否**（else 分支才 chat） | L322–326 |

**绕过风险：代码审查未发现绕过路径 → PASS（静态）。**  
真实 P1 运行时 live 阻断触发：**NOT_VERIFIED**（未做故障注入）。

---

## 2. Mock 测试（29 passed）

文件：`p1/tests/test_v12_m3_fix01_gate.py`、`test_v12_oprime_messages.py`、`test_v12_r22_edit_safety.py`

| ID | 场景 | 预期 | 实际 n_chat | 结果 |
| --- | --- | --- | --- | --- |
| T1 | 正常 ET FULL | 允许 | 2 | PASS |
| T2 | 缺 must_full | 阻断 | 0 | PASS |
| T3 | VP/vproof 验证失败 | 阻断 | 0 | PASS |
| T4 | ET 未 FULL 验证 | 阻断 | 0 | PASS |
| T5 | CandidateFull 失败 | 阻断 | 0 | PASS |
| T6 | messages≠pre_send | 拒绝 | 0（verify 路径） | PASS |
| T7 | force 后仍失败 | 阻断 | 0 | PASS |
| T8 | 恢复成功 | 允许 | 2 | PASS |

---

## 3. 真实执行历史（P0，参考非 P1）

- 64 步 `pre_send.ok`、`edit_target_full_verified` 全 true  
- INSUFFICIENT **0** → live 阻断 **NOT_VERIFIED**  

---

## 4. 结论

**VP Runtime Gate：PASS（Mock + 静态单入口）。**  
**Live INSUFFICIENT 触发：NOT_VERIFIED。**
