# EXPERIMENT_INDEX — 实验与配置索引

状态：**ACTIVE · 索引（不复制原始数据）**  
生成：2026-11-18  
原则：原始 run/日志与衍生统计分开；原始配置与超限恢复配置分列；**不覆盖历史**。

## 1. 主实验（V13E）

| ID | 内容 | 路径 | 备注 |
| --- | --- | --- | --- |
| **V13E 主实验** | 双模型、多臂、56 repository-editing 合成任务 | `p1/experiments/v13e_sah/`, `v13e_crossmodel/` | 旗舰定位；`definitive56.*` |
| 臂 | F / PROJ(S1) / SAH(S1+S2) / MOFF 等 | `v12/config.py` | 架构 ID 见 `run_p1_v12.py` |
| 预注册 | crossmodel 草稿与冻结 | `p1/docs/v13e_crossmodel_preregistration_draft.md`, `prereg_freeze.json` | 以冻结文件为准 |
| 模型 | DeepSeek 主跑 + Qwen 复现（以 run_meta 为准） | 各 `runs/*/run_meta.json` | 勿与探索轮混并 |
| 统计 | bootstrap seed/B、非劣界等 | 预注册 + 分析脚本 | 与 V12F §1.3 同口径处已核对 |

## 2. V12-F 确认性批次

| ID | 路径 | 说明 |
| --- | --- | --- |
| P1 确认性 | `p1/experiments/p1_validation/` | 预注册协议 |
| P2 消融 | `p1/experiments/p2_ablation/` | O′/redact 等 |
| P3-A / crossmodel Qwen | `p3_crossmodel_qwen/` | 补记后执行 |
| 总审计 | `V12F_final_validation_and_submission_report.md` | 冻结哈希、样本量、口径 |

## 3. 扩展与故障注入

| ID | 路径 | 定位 |
| --- | --- | --- |
| **P1_TRANSFER** | `p1/experiments/v13e_p1_transfer/`, `v13e_p1_swebench/`；顶层 `P1_TRANSFER_PROTOCOL_AND_RESULTS.md` | **扩展验证**，10 实例 SWE-bench Lite 子集；**不取代** V13E 主实验；非官方 leaderboard |
| VSO 故障注入 | `p1/experiments/vso_fault_injection/` | 受控注入；非生产自然故障率 |
| 双 Token | `p1/experiments/dualtoken_ablation/` | 探索；结论见报告 |
| Robustness | `V13E_CLUSTER_ROBUSTNESS_AUDIT.md`（顶层） | 聚类稳健性审计 |

## 4. 任务集（只读，禁止当草稿改）

| 目录 | 用途 |
| --- | --- |
| `p1/tasks/`, `tasks_p1_validation/` | P1 等冻结题集 |
| `tasks_v13_holdout/`, `tasks_v13a_*`, `tasks_v13d_chain/` | 筛选/holdout/链式 |
| `tasks_transfer_v1/` | Transfer |
| `tasks_independent_v1*` | 独立任务集 |

manifest：`p1/manifests/*.json`

## 5. 配置与恢复

| 类型 | 记录位置 | 规则 |
| --- | --- | --- |
| 冻结配置 | 各 `run_meta.json`, `config_sha256`, `code_snapshot.json` | 不改写 |
| 原始超限/失败 | episode 内 `INSUFFICIENT`、`*.err.log`、ABORTED 目录 | **保留**，与成功 run 分列 |
| 恢复/补跑 | 目录名含 resume/repair、或单独 run 目录 | **新 run**，不覆盖旧数据 |
| 衍生统计 | `analysis.json`, `*_report.md`, 顶层 STATS_*.md | 与原始 logs 分开 |

## 6. 模型与重复

- 以各实验预注册与 `run_meta` 为准（temperature/seed/max_tokens/重复次数）。
- V12F：多轮重复与 Holm 校正见总报告。
- P1_TRANSFER：3 reps × 双模型；Qwen 曾用 `qwen3.8-flash`（协议已披露）。

## 7. 禁止事项（实验口径）

1. 不用 P1_TRANSFER 替换 V13E 主实验叙事  
2. 不把 MOFF 写成外部 Coding Agent  
3. 不把本地重实现写成原作者官方实现  
4. 不把目标/预期写成已实现结果  
5. 不把 `cached_tokens` 写成 KV 显存  
