# MECHANISM_VISIBILITY_PROOF — VP（旧名 O′）

状态：**ACTIVE · VERIFIED（代码）**  
生成：2026-11-18  
正式名：**VP = Visibility Proof**；历史文档中的 **O′** 映射到本概念（不改原文）。

## 1. 解决的问题

V1.0 使用 `history_sent` 全局记账，与**当前 messages 实际内容**不一致，导致不安全省略风险。  
V1.1 引入 VP：只信任**当前对话中仍可见**的文件内容哈希。

## 2. 实现位置

| 组件 | 路径 |
| --- | --- |
| 核心谓词与追踪 | `p1/scripts/v11/visibility.py` |
| V12 装配接入 | `p1/scripts/v12/assemble.py`（`safe_omission` 调用） |
| 消息侧校验 | `p1/scripts/v12/messages_visibility.py` |
| 审计字段 | `n_verified_safe_omissions`（`p1_common.py` / runner） |
| 单测 | `p1/tests/test_v11_visibility.py`, `test_v12_oprime_messages.py` |

## 3. 谓词（代码原文）

```text
allow_omit 仅当：
  hash_match
  ∧ previously_visible_in_messages
  ∧ file_not_in_current_ctx
  ∧ not tombstoned
  ∧ not force_expand
```

失败原因示例：`force_expand`、`validity=tombstoned`、`already_in_current_context`、`no_visible_proof_in_messages`。

## 4. 正确性边界（论文禁句对照）

| 可写 | 不可写 |
| --- | --- |
| 在 messages 可见面内，内容哈希匹配时允许省略 | VP 发现了全部相关文件 |
| 降低重复内联；与 P2 中 O′≈−398 tok/集同向 | 消除所有 TOCTOU / 竞态 |
| 发送前 PreSendCheck 失败则 fail-closed | VP 保证语义完全等价于全量历史 |
| S1 保持末版 ⇒ 与 VP 提取字段一致（已离线重放核对处） | 投影=任意语义等价 |

## 5. 实验依据（索引，不重算）

- V1.1 引入与失败分析：`p1/docs/v1.1/v1.1_architecture_design.md`, `v1.1_failure_analysis.md`
- V12-F P2 消融：O′ 贡献主导（见 `p1/experiments/p2_ablation/p2_ablation_report.md` 与 V12F 总报告 §1.4）
- VSO 故障注入：`p1/experiments/vso_fault_injection/`，设计 `p1/docs/vso_fault_injection_evaluation_design.md`
- V13E O′ 等价离线：`v13e_sah/verify_projection.py`, `replay_report.json`（设计稿声称 0 失败；引用时以该文件为准）

## 6. 与 S1 关系

S1 **不替代** VP；S1 折叠历史后仍走同一 `safe_omission`/PreSendCheck 路径。  
证据映射主轴：**VP 与 F+S1**；S2 仅辅助。
