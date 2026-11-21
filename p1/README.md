# VAM-Coder P1 实验脚手架

P1 阶段的目的是以较低成本验证研究假设、排除无效设计，并为更大规模实验
提供依据。任务集、指标与判定规则在 `tasks/tasks.json` 中预注册；无论结果
正负，原始记录均保留在 `p1/results/runs/`。

## 研究假设（预注册）

> 在多轮代码修改过程中，版本感知的记忆失效机制与按需读取策略，能否在
> 维持任务质量的同时，降低重复读取和过期记忆带来的成本？

P1 用本地小模型检验机制链路是否成立，而不是检验方法绝对性能。

## 四种基线（共用同一任务集 / 模型 / 测试判定）

| 基线 | 每步给模型的上下文 | 记忆行为 |
| --- | --- | --- |
| `memory_off` | 工作区全部当前 `.py` 源码 | 无持久记忆 |
| `symbol_full_read` | 索引中每个存活符号所在文件的完整源码 | 每步全量重读，无版本感知 |
| `fixed_summary` | 仅 episode 开始时冻结的符号摘要 | 摘要永不刷新、不失效 |
| `vam_coder` | 按冻结 P0 路由决策装配 | sync（失效）→ route → 按决策装配 |

`vam_coder` 的装配语义：

- `EXPAND` → 读取该符号所在文件的**当前完整源码**（P0 只输出决策，读取由本脚手架执行）；
- `COMPRESS` → 使用 P0 存储的摘要；
- `REUSE_KV` → **文本上下文复用代理**：仅当该符号当前内容哈希与对话中
  已发送内容一致时才从提示词中省略；否则回退为读取当前源码；
- `DROP` → 不提供。

### 能力边界（必须与结论一起报告）

- `REUSE_KV` 不是真实 KV 仓。省略文本后，llama-server / Ollama 对多轮
  对话前缀有**服务端** KV 复用，这不等同于 VAM 论文中的跨请求记忆 KV。
  本阶段报告的是 token / 时延 / 测试结果，**不宣称**测到真实 KV 显存收益。
- 摘要来自 P0 的 docstring 抽取（`simulate_summary`），不是模型生成。
- 评测只统计 `eval/stepN` 下的 pytest；eval 目录复制到临时目录运行，
  与模型可写工作区隔离，模型上下文中也不出现测试代码。

## 使用

前置：P0 依赖已安装（见仓库根 `requirements.txt`）；有一个 OpenAI 兼容
推理端点（本机推荐 `start_server.bat` 启动 llama-server →
`http://127.0.0.1:8080/v1`；Ollama 用 `http://127.0.0.1:11434/v1`）。

```bash
# 1) 先验证装配链路（不调用模型）
python p1/scripts/run_p1.py --episode inventory_dependency --dry-run

# 2) 单 episode × 四基线
python p1/scripts/run_p1.py --episode inventory_dependency \
    --endpoint http://127.0.0.1:8080/v1 --model qwen2.5-coder-1.5b

# 3) 全量固定任务集
python p1/scripts/run_p1.py --episode all --baselines all \
    --endpoint http://127.0.0.1:8080/v1 --model qwen2.5-coder-1.5b
```

常用参数：`--max-tokens`（默认 1024）、`--temperature`（默认 0）、
`--seed`（默认 0）、`--budget-tokens`（路由预算，默认 4096）、
`--timeout` / `--eval-timeout`、`--out`（指定结果目录）。

## 输出与指标

```
p1/results/runs/<时间戳>_<model>/
  run_meta.json        任务集 sha256、git rev、参数、能力边界、预注册规则
  per_step.csv         逐步骤原始指标
  summary.csv          episode × baseline 聚合
  episodes/<ep>/<baseline>/
    workspace/         模型改完后的代码
    store.db, logs/    P0 记忆库与决策/失效日志（vam_coder）
    steps/<step>/      context.txt, prompt.txt, response.txt,
                       apply.json, eval_output.txt, result.json
    episode_summary.json
```

`per_step.csv` 列（**分列报告，不得互相替代**）：

- 质量：`eval_success`（该步隔离测试是否通过）
- 成本：`prompt_tokens` / `completion_tokens` / `total_tokens`
  （优先用推理端返回的 usage，缺失时估算并标记 `usage_source=estimate`）
- 延迟：`t_model_ms`（模型调用）与系统开销
  `t_sync_ms` + `t_route_ms` + `t_assemble_ms`（P0 同步/路由/装配）
- 机制：`n_expand` / `n_reuse_kv` / `n_compress` / `n_drop`、
  `n_stale` / `n_unverified` / `n_tombstoned`、`reuse_omitted`
  （REUSE_KV 代理实际省略的符号数）

“有效”与“值得部署”分开解读：token 下降不代表端到端延迟下降。

## 当前任务集（玩具集，不能支撑论文结论）

| episode | 重点 | 步骤 |
| --- | --- | --- |
| `inventory_dependency` | 依赖失效：`available()` 变更使 `can_fulfill()` 进入 unverified | 修正可售计算 → 引入 BUFFER 缓冲 |
| `rename_symbol` | 墓碑：`compute` → `compute_double`，旧名不可再用 | 重命名并更新调用方 → 修改 `helper()` |
| `stale_summary_trap` | 过期摘要陷阱：docstring 漂移后固定摘要给出错误单价 | `UNIT` 10→12 → 写死当前单价实现 `fast_price` |

扩充任务集时：只新增 `tasks/<id>/`（`project/` + `eval/stepN/`）并在
`tasks.json` 追加条目；**不要**按结果回头修改已冻结的 episode。
建议扩到 20–30 个 episode、覆盖跨文件依赖 / 签名变化 / 删除 / 同名消歧 /
无关修改，并做重复实验后再谈结论。

## 扩展到 P2 / P3（本目录不做，仅记录接口）

- P2 消融：以 `fixed_summary` / `symbol_full_read` 作为“去版本感知 / 去路由”
  变体，同一入口加 `--baselines` 即可；更大仓库与多轮修改只需换任务集。
- P3 强模型：换 `--model` / `--endpoint`；若要主张真实 KV 收益，需接入可
  测量缓存与显存的推理环境，并替换 `CAPABILITY_NOTES` 中的代理声明。

## Windows 路径说明

P0 的 `file_path` 语义为相对仓库根的 posix 路径。本脚手架在
`p1_common.posix()` 中统一把 `\` 规范化为 `/`，并应用于决策装配与
`FILE:` 块解析，保证 Windows 下反斜杠路径不会导致上下文装配或文件写入错位。
