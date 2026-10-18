# P1 测量脚手架最小修复记录（2026-10-18）

依据：`p1/results/audit_p1_first_run_20261018_123047.md` G.1 已证实问题。
原则：不修改冻结 P0（`a31a0c1`）；不删除/覆盖任何历史 run；不弱化测试。

## 修复优先级（审计结论 → 实施范围）

| 优先级 | 问题（审计编号） | 本轮是否实施 | 说明 |
| --- | --- | --- | --- |
| P0 | raw_usage 未落盘，cached_tokens 丢失（G.1-5） | ✅ 实施 | `result.json` 增加 `raw_usage` 字段 |
| P0 | 环境元数据不全、脚本/判据无哈希锚点（G.1-3/4/6） | ✅ 实施 | run_meta 增加：P1 脚本哈希、eval 目录哈希、`/version` 与 `/v1/models` 尽力探测 |
| P0 | 初始 sync 记账不自洽（G.1-8） | ✅ 实施 | 去掉冗余 episode 级初始 sync；fixed_summary 改为在 step1 内 sync 并冻结摘要 |
| P0 | 基线执行顺序固定（G.1-7 的可行动部分） | ✅ 实施 | 按 episode 序号轮换基线顺序（确定性轮换，不引入随机源） |
| P1 | 完整 messages 未保存（G.1-10） | ✅ 实施 | 每步保存 `messages.json`（完整请求消息列表） |
| P2 | 历史策略语义（G.1-9） | ❌ 不在本轮改 | 属实验设计变更，会破坏与首轮的可比性；列入 P1-v1.0 阻塞项 |
| P2 | reuse_omitted 低估（G.2-2）、est_tokens 校准（F.1-4） | ❌ 不在本轮改 | 需与 v1.0 schema 一并设计 |
| — | 冻结 P0 本体 | ❌ 不改 | 审计未发现必须改 P0 才能修复的正确性问题 |

## 修改前后行为对照

| 行为 | 修改前 | 修改后 |
| --- | --- | --- |
| token 明细 | 仅 prompt/completion/total（API usage） | 另存 `raw_usage` 原始 JSON（含 cached_tokens，若服务端返回） |
| 环境记录 | model 别名、endpoint、git_rev(P0) | 增加 p1 脚本 sha256、每步 eval 目录 sha256、服务端 /version 与 served model（探测失败则记 `null`，不伪造） |
| fixed_summary 计时 | episode 级初始 sync 在步计时器外，`t_sync_ms` 与 `t_step_ms` 口径冲突（审计 F.1-1） | step1 内完成 sync+冻结，全部计入步计时 |
| symbol_full_read / vam_coder 初始 sync | 多做一次冗余 sync，且成本从 CSV 消失 | 删除冗余 sync；每步一次 |
| 基线顺序 | 恒为 memory_off→…→vam_coder | 按 episode 索引轮换；顺序写入 run_meta `baseline_order` |
| 请求重建 | 仅 `prompt.txt`（末轮 user） | 另存 `messages.json`（system+历史+本轮） |

## 回归测试

新增 `p1/tests/test_p1_harness.py`（不依赖模型服务）：
posix 规范化、FILE 块解析、路径越界/eval 保护、REUSE_KV 哈希命中省略、
历史缺失回退、同文件 EXPAND 去重、fixed_summary 无源码块。

**测试新增时抓到的额外缺陷（已修）**：`apply_blocks` 原用
`lstrip("./")` 规范化路径，会把 `../evil.py` 与 `/abs/x.py` 洗成工作区内
相对路径（未逃逸沙箱，但拒绝逻辑失效）。已改为逐段剥离 `./` 前缀并显式
拒绝绝对路径与 `..` 段。修复后 `pytest p1/tests` 8 passed。

## 验证记录

- `python -m py_compile p1/scripts/run_p1.py p1_common.py` → exit 0
- `python -m pytest p1/tests -q` → 8 passed, exit 0
- `python p1/scripts/run_p1.py --episode stale_summary_trap --dry-run` → exit 0
  （新 run `20261018_123853_*`：messages.json 存在；eval 哈希 6 条；
  server 探测失败如实记 URLError；fixed_summary 的 t_sync 已落在
  t_step 内：17.39 ≤ 19.65ms）
- 未修改冻结 P0；未触碰任何历史 run 目录。
