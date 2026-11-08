# VP / INSUFFICIENT 安全门禁集成测试报告

性质：**Unit + Mock 集成**；**无**真实 llama-server / 无 P1 样本。

## 测试矩阵

| ID | 场景 | 证据 | 调用次数 | 结果 |
| --- | --- | --- | --- | --- |
| T1 | 正常 EditTarget FULL → 允许 | `test_integration_pass_allows_chat` | **2** | PASS |
| T2 | 缺必须文件 → INSUFFICIENT | `test_integration_missing_required_chat_zero` | **0** | PASS |
| T3 | verify 失败 → 阻断 | `test_integration_second_fail_chat_count_zero` | **0** | PASS |
| T4 | E 无法验证 FULL | `test_integration_edit_target_fail_chat_zero` | **0** | PASS |
| T5 | C 错误省略/验证失败 | `test_integration_candidate_fail_chat_zero` | **0** | PASS |
| T6 | 与 pre_send 一致性 | `test_v12_oprime_messages` + r2.2 verified 字段 | n/a（断言 messages） | PASS |
| T7 | force_full 后仍失败 | 二次 verify 路径 | **0** | PASS |
| T8 | 恢复成功仍允许 | `test_integration_force_full_recover` | **2**（revised） | PASS |

套件：`test_v12_m3_fix01_gate.py` **10 passed**；相关套件合计见门禁运行记录。

## 术语

- 日志/论文：**VP / vproof**（Visibility Proof for Safe Omission）  
- 代码历史名：O′ 仅追溯  

## 边界

- **不是**真实模型验证  
- P0 中 INSUFFICIENT=0 → live 阻断触发 **NOT_VERIFIABLE**  
- 阻断正确性以本 Mock + 代码路径（`should_call_model` 单入口）为准  
