# 数据采集与统计复算

## 1. 每步可追溯字段（现有 runner）

| 字段 | 位置 | P0 验证 |
| --- | --- | --- |
| context / messages | steps/* | 有 |
| pre_send_check (VP/vproof) | steps/* | 有 64/64 |
| injection audit | logs/ | 有 |
| response / eval_output / result | steps/* | 有 |
| tokens | result / per_step | 有 |
| failure_class | **分析后 CSV**（非 runner 内嵌） | post_review failure_analysis.csv |
| workspace pre/post/diff | — | **缺** → 见 workspace 报告 |

## 2. 统计复算（P0 原始数据，未改）

| 指标 | E | F | G | H | 与 claim |
| --- | --- | --- | --- | --- | --- |
| ESR | 4/8 | 3/8 | 4/8 | 4/8 | 一致 |
| SPR | 9/16 | 8/16 | 9/16 | 9/16 | 一致 |
| TPAE | 539.4 | 542.1 | 556.5 | 542.5 | 一致 |
| TPSE | 1078.8 | 1445.7 | 1113.0 | 1085.0 | 一致 |
| FETC_total | 2026 | 2599 | 2089 | 2013 | 一致 |

来源：`per_step_all.csv` 按 task 合取 success、token 求和。

## 3. 边界规则

| 规则 | 状态 |
| --- | --- |
| 零成功 TPSE=NA/∞ | method/prereg **已定义**；本批未触发 |
| 零失败 FETC_mean=NA | **已定义**；本批未触发 |
| 重试累计 token | 预注册有；runner **无自动重试** |
| cached_tokens ≠ KV 节省 | 预注册禁止；报告遵守 |
| 模型错误 vs 安全错误分类 | failure_analysis 分列 MODEL_* / VP_* |
| 禁止“显著优于/证明有效/已证非劣” | 审查报告遵守 |

## 4. 局限

- n 小；CI 宽；**不支持**强非劣或架构有效结论。  
- P1 尚未执行，本报告为 **P0 复算 + 采集完备性**。

**Data Collection & Metrics：PASS（除 workspace pre/post 为 CONDITIONAL 项）**
