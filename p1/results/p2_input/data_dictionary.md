# P2 输入数据字典（formal_runs.csv）

| 列 | 含义 | 来源 |
| --- | --- | --- |
| run_id | 正式 run 目录名 | 目录名 |
| block | A（keep/条件A）或 M（redact/条件M） | run_meta.history_policy |
| history_policy | keep / redact | run_meta |
| repetition_id | rep 编号（1..3） | run_meta.rep |
| task_id | v1_* 任务 ID | per_step.episode |
| baseline | 五组基线之一 | per_step.baseline |
| step | step1/step2 | per_step.step |
| eval_success | 1/0 | per_step |
| prompt/completion/total_tokens | API 真实计数 | per_step（usage=api） |
| cached_tokens | 服务端前缀缓存命中；缺失为空 | result.raw_usage.prompt_tokens_details |
| cached_tokens_missing | 1=服务端未提供 | 派生 |
| history_file_blocks / history_code_chars | 请求历史中 FILE 块数/代码字符 | per_step |
| omitted_tokens_est | 该步 assemble_audit 中估算省略 token 合计（**估算**） | result.assemble_audit |
| verified_safe_omission | 该步已验证安全省略文件数（谓词 O） | result.n_verified_safe_omissions |
| model_latency_ms | 单步模型 HTTP 墙钟 | per_step.t_model_ms |
| episode_latency_ms | 单步端到端（含 eval/写盘） | per_step.t_step_ms |
| mechanism_triggered | 该 run 内该任务必需机制事件是否全部触发 | mechanism_check.json |
| usage_source / error | 计数来源与错误 | per_step |

**纪律**：omitted_tokens_est ≠ 真实节省；cached_tokens 是服务端行为，不等于
VAM 记忆仓；REUSE_KV 是文本省略代理。
