# Evidence Gaps（P0 后审查）

只读记录；**不**补造历史哈希。

## G1. 实验前 workspace 全量 SHA 对账

| 项 | 说明 |
| --- | --- |
| 状态 | **EVIDENCE GAP** |
| 已有 | 阶段 B `episode_manifest.json` 含 `initial_workspace_hash`（源 project 清单）；执行时每集独立 copytree |
| 缺失 | execution/ 下 **未** 在 step0 落盘逐文件 SHA 对照表 |
| 影响 | 隔离主要靠目录结构 + 源冻结；无法事后证明“开始时刻字节级等于源” |
| 建议 | 后续 P1 前：执行器在 step0 写 `workspace_manifest.json`（文件→SHA256+目录 hash）；**禁止**用当前事后清单冒充实验前证据 |

## G2. INSUFFICIENT 阻断未在真实模型路径触发

| 项 | 说明 |
| --- | --- |
| 状态 | 本轮 **0** 次阻断 |
| 已有 | 单测 `test_v12_m3_fix01_gate` mock 调用次数=0 |
| 缺失 | 真实 runner 上“verify 失败 → 零请求”的 **live** 正样本 |
| 建议 | 可选：诊断用故障注入（不进正式指标）；或接受单测+代码审查 |

## G3. RFS01_F step1 UNDETERMINED

| 项 | 说明 |
| --- | --- |
| 状态 | 1 条失败 primary=UNDETERMINED |
| 证据 | response 写入 mode.py 为 `"""Mode."""` 为主；需对照任务“改 describe 返回值”是否算完成 |
| 建议 | 人工读 `evidence_path` + eval；确认后改分类（本审查不改数据） |

## G4. cached_tokens / prefill 深度

| 项 | 说明 |
| --- | --- |
| 状态 | 本审查以 prompt_tokens 为主；未强制解析每条 raw cached |
| 建议 | P1 若报 prefill：分列 cached，禁止当 KV 节省 |

## G5. CandidateFull 召回

| 项 | 说明 |
| --- | --- |
| 状态 | 保守策略按审查保留；P0 未以 C 触发率为主指标 |
| 建议 | 不在本轮“修召回” |
