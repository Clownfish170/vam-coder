# P1 首轮真实运行纪要（2026-10-16）

环境：本地 llama-server（qwen2.5-coder-1.5b-instruct-q6_k，ctx 8192，
OpenAI 兼容 `http://127.0.0.1:8080/v1`），temperature=0，seed=0，
max_tokens=1024。任务集 `p1-v0.1.0`（3 episode × 2 步 × 4 基线）。

本纪要只记录测量链路是否成立与失败案例，**不构成方法优劣结论**
（玩具任务集 + 单次运行 + 1.5B 模型）。

## 结果总览（步骤级通过数，最新一轮）

| episode | memory_off | symbol_full_read | fixed_summary | vam_coder |
| --- | --- | --- | --- | --- |
| inventory_dependency | 1/2 | 1/2 | 0/2 | 1/2 |
| stale_summary_trap | 2/2 | 2/2 | 0/2 | 2/2 |
| rename_symbol | 2/2 | 2/2 | 1/2 | 2/2 |

原始数据：`p1/results/runs/20261016_194629_*`（inventory）、
`20261016_194723_*`（trap）、`20261016_194913_*`（rename）。
更早的失败轮次（含修正前的错误测试口径）一并保留，未删除。

## 测量链路结论

- 四基线均可在同一任务集/模型/判定下端到端运行，逐 token（API usage）、
  逐延迟、逐系统开销（sync/route/assemble 分列）均已落盘。
- `vam_coder` 的机制在真实推理中生效：
  - inventory step2：`available` 变化 → stale→EXPAND；
    `can_fulfill` 依赖闭包 → unverified→EXPAND；
    未变化的 `catalog_value` → REUSE_KV 并从提示词省略（`reuse_omitted=1`）。
  - trap step2：`price` 因 step1 修改变为 stale → EXPAND 重读到
    `UNIT = 12`，写出 `qty * 12`，测试通过。
- `fixed_summary` 在 trap 中按冻结摘要（含过期 “(=10)”）行动：
  step2 把 `fast_price` 写进错误文件且未写死单价，0/2；
  这正是过期记忆的失败模式，说明失效机制有可检验的对照差异。

## 已知问题与限制

1. **模型能力上限**：inventory step2 对所有提供源码的基线均失败——
   1.5B 加了 `BUFFER = 5` 却未使用（写成 `max(..., 0)`）。这是模型问题，
   不是链路问题；P1 的意义正是用小模型暴露这类上限。
2. `REUSE_KV` 是文本上下文复用代理（见 `run_meta.json` 的
   `capabilities`），不宣称真实 KV 仓收益。
3. 单次运行、任务集只有 3 个玩具 episode，不可用于论文结论。
   扩到 20–30 episode、重复实验后再分析。
4. 首轮曾发现两处**评测口径错误**（inventory step1 零下限、
   rename step2 断言值），已修正并重跑；修正前结果保留在更早的
   runs 目录中，避免“按结果改测试”的嫌疑需要时可复核。

## 下一步（属于后续工作，不在本轮范围）

- 扩充任务集并冻结为 `p1-v1.0`；对每 episode 做 3–5 次重复。
- 分析 `per_step.csv`：token 差异主要来自 REUSE_KV 省略 vs 全量重读；
  系统开销（sync+route+assemble）与模型延迟分开报告。
- inventory 类任务换更强模型验证是否仍是能力上限。
