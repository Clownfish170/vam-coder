# P1-v0.2 加固验收与冒烟报告

时间：2026-10-18（UTC+8）  
分支：`p1/v0.2`（`b1a0218` + `24b2470`，父提交 = 冻结 P0 记录 `c1be8d2`；P0 三提交未动）  
范围：工程加固验收 + 1 个 episode 的 dry-run 与真实模型 smoke。**未启动** 20–30 episode 正式实验。

## 1. 命令与退出码

| # | 命令 | 退出码 | 结果 |
| --- | --- | --- | --- |
| 1 | `python -m py_compile p1/scripts/{run_p1,p1_common,make_manifest,check_run_integrity}.py` | 0 | COMPILE_OK |
| 2 | `python -m pytest p1/tests -q` | 0 | **20 passed**（含 v0.2 新增 12 项） |
| 3 | `python -m pytest tests -q`（冻结 P0） | 0 | **86 passed** |
| 4 | `python scripts/run_p0_scenario.py` | 0 | **ALL PASSED (6/6)** |
| 5 | `python p1/scripts/make_manifest.py --name p1_v0.2_manifest` | 0 | 清单生成（4 脚本 / 6 eval / 3 project，含逐文件哈希） |
| 6 | `python p1/scripts/run_p1.py --episode stale_summary_trap --dry-run --rep 1` | 0 | run `20261018_130448_…_rep1` |
| 7 | `python p1/scripts/check_run_integrity.py <dry-run run>` | 0 | **8 checks, 0 FAIL** |
| 8 | 真实 smoke：`run_p1.py --episode stale_summary_trap --rep 1 --endpoint http://127.0.0.1:8080/v1 --model qwen2.5-coder-1.5b` | 0 | run `20261018_130627_…_rep1` |
| 9 | `check_run_integrity.py <真实 run>` | 0 | **8 checks, 0 FAIL** |
| 10 | `git commit`（分支 `p1/v0.2`） | 0 | 29 文件入库；`p1/results/runs/` 与 `.cache/` 被 ignore |

环境：llama-server（本机启动，`qwen2.5-coder-1.5b-instruct-q6_k.gguf`，
ctx 8192，`--parallel 1`）；smoke 结束后服务已停止。

## 2. 任务 1–8 落地核对

| 任务 | 状态 | 证据 |
| --- | --- | --- |
| 1 版本与评测冻结 | ✅ | `p1/manifests/p1_v0.2_manifest.json`（不可覆盖）；run_p1 启动校验，不一致退出 3；run_meta 记录 tasks/eval/project/script 哈希 + manifest_check |
| 2 环境与模型元数据 | ✅（部分字段服务端不提供） | 真实 run_meta：gguf_sha256=`9b05dce8…`（computed）、quant=`q6_k`、server_ctx=`8192`（/props）、served model=gguf 全路径；`/version` 返回 404 → version=null（如实）；`server_args`/`parallel_slots`=unknown（未探测到，不编造） |
| 3 原始请求与 usage | ✅ | 每步 `messages.json` + `request.json`（params、起止时间、HTTP 200、messages_sha256、usage_raw）。样本：vam step1 `usage_raw.prompt_tokens_details.cached_tokens=168`（服务端前缀缓存命中被**原样捕获**，v0.1 丢失该字段）。无鉴权头记录（`auth_headers_logged:false`） |
| 4 计时口径 | ✅ | `t_initial_sync_ms` 单列（真实 run：记忆基线 21–46ms，memory_off=0）；`t_episode_ms=t_initial+Σt_step`；一致性检查无负 gap（v0.1 的 fixed_summary 异常已消除） |
| 5 顺序与历史策略 | ✅ | `(ep_idx+rep)%N` 轮换（rep=1 → 队首 symbol_full_read）；`baseline_orders.json`；统一 `trim_history`（max_history_chars=24000，四基线同一函数）；每步记录 n_messages/history_tokens_est/context_tokens_est |
| 6 过期摘要对照 | ✅ | 新增对照 `refreshed_summary`（每步刷新摘要、无版本门控）。真实 smoke：fixed 0/2、refreshed 0/2（1.5B 在“只有摘要”下均失败——差异未显现属模型能力，判据未改）。trap step1 指令禁改 docstring + eval 断言（任务集 `p1-v0.2.0`，新清单） |
| 7 复用量三口径 | ✅ | CSV/result 新列：`reuse_decisions / reuse_omitted / reuse_omitted_files / reuse_omitted_bytes / reuse_without_omission / expand_included_bytes`；同文件 EXPAND 带回 REUSE 的场景有单测覆盖 |
| 8 测试与验收 | ✅ | 见上表 2/3/4；检查器 8 项在 dry-run 与真实 run 均 0 FAIL |

## 3. 真实 smoke 结果（stale_summary_trap，rep=1，单次，不可作结论）

| 基线 | step1/step2 | 累计 API tokens | 备注 |
| --- | --- | --- | --- |
| symbol_full_read | 0 / 1 | 669 | |
| fixed_summary | 0 / 0 | 597 | |
| vam_coder | 0 / 1 | 715 | step2 两个符号均 stale/unverified → EXPAND（reuse_omitted=0，符合预期） |
| refreshed_summary | 0 / 0 | 597 | 对照 |
| memory_off | 0 / 1 | 657 | |

**重要观察**：step1 在**全部**基线（含给源码的基线）失败，原因均为
`test_docstring_unchanged`——1.5B 无视“不要改 docstring”指令，把
`(=10)` 顺手改成 `(=12)`。这证明 v0.2 判据确实堵住了历史混淆，同时说明
该约束对 1.5B 是高难度项。**按预注册原则不回调判据**；v1.0 任务集设计时
可保留为已知难度或在新版本中重新设计（新清单），不得静默放松。

## 4. 代码变更摘要（相对 v0.1）

- `run_p1.py`：整体升级（清单校验、run_id 防覆盖、rep 轮换、初始 sync 单列、
  request.json、五基线、扩展 CSV、服务/模型/硬件元数据）。
- `p1_common.py`：ChatResult 审计字段、HTTPError 处理、复用量三口径、
  `trim_history`、`assemble_refreshed_summary`、tokens 估算标注。
- 新增：`make_manifest.py`、`check_run_integrity.py`、
  `tests/test_v02_hardening.py`（12 项）、`docs/p1_v0.2_protocol.md`、
  `docs/p1_v0.2_schema.md`、`manifests/p1_v0.2_manifest.json`。
- 任务集：`p1-v0.2.0`（trap step1 指令 + docstring 断言）。历史 v0.1 run
  的 tasks_sha256=`8213772a…` 与新版本 `7afa7409…` 可区分。
- 冻结 P0：零改动（86 tests + 6/6 scenario 复验）。

## 5. 已知限制 / 未完成项

1. `/version` 在当前 llama-server 构建上 404 → `server_probe.version=null`；
   启动参数与并行槽位需 `--server-args/--server-ctx` 人工补或保持 unknown。
2. `git_dirty=true` 来自未跟踪的 `results/runs/`、`.cache/`、
   `llama_server.log`（有意不入库）。
3. `refreshed_summary` 与 `fixed_summary` 的差异在 1.5B 上未显现（双双 0/2），
   需更强模型或更易摘要任务才能分离。
4. 真实 smoke 仅 1 episode × 1 rep；无统计意义。
5. 完整性检查器第 8 项对 EXPAND↔上下文的交叉核对目前以“context 头出现在
   最终 user 消息”为主，符号级逐条映射仍可加强。
6. 未实现 `--warmup N` 预热丢弃（v1.0 待办，见 P1_V1_PLAN 阻塞项）。

## 6. 正式实验前仍未关闭的阻塞项（沿用 P1_V1_PLAN B1–B4 + 新增）

- B1 服务元数据：已基本可探测（version 字段除外）；正式 run 前再校验一次。
- **B2 历史策略解释口径**：统一保留 assistant 历史已实现且四基线一致，但
  “无源码基线可从自身历史看到先前写过的代码”这一影响必须写进任何结果解释。
- B3 重复预算：R≥3 × 24 episodes × 5 基线的时间/电力预算未批。
- B4 Git：P1 已在 `p1/v0.2` 分支；正式实验前应合并/打 tag 并以 tag 哈希为锚。
- **B5（新增）**：trap 类“禁改 docstring”约束对 1.5B 全线失败——v1.0 设计
  阶段决定：保留为难度特性，或在**新任务集版本**中改为不依赖模型自律的
  结构（例如把陷阱数值放在模型必须删除的过期注释文件中）。不得在结果出来后
  修改已冻结判据。
