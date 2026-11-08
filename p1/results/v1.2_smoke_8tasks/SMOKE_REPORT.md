# VAM-Coder v1.2-r2.1 Smoke Test 总报告（8 任务 × 带模型）

状态：**Smoke 完成**。输出目录：`p1/results/v1.2_smoke_8tasks/`  
范围：预注册 P0 子集 8 任务，R=1；臂 **D(v1.1) + E/F/G/H**。  
**本 Smoke 不能证明准确率或效率优势**；不得宣称 V1.2 优于 memory_off。

---

## 1. Smoke Test 总报告

| 项 | 值 |
| --- | --- |
| 模型 | qwen2.5-coder-1.5b-instruct-q6_k @ 127.0.0.1:8080 |
| API 请求 | E/F/G/H 64 + D 16 = **80** |
| HTTP/模型错误 | **0** |
| 单元测试（前置） | 20 passed |
| 跑前 bug | 首次 E/F/G/H **未接 Eval** → `v1.2_smoke_8tasks_noeval_buggy/`；已修 `run_p1_v12.py` 并重跑 |

### 1.1 Episode 成功率（两步全过）— **仅冒烟参考**

| 臂 | ESR | 备注 |
| --- | --- | --- |
| D v1.1 | **4/8** | 对照 |
| E | 1/8 | |
| F | 1/8 | |
| G | 1/8 | |
| H | 2/8 | |

Step 通过（E/F/G/H）：E 6/16，F 5/16，G 6/16，H 7/16。  
失败以 **NO_EDIT**（25 次）与 step2 塌陷为主。

**禁止**据此下“V1.2 更差/更好”的统计结论（n 小、1.5B、任务难）。

### 1.2 Token（含全部实际请求）

| 臂 | TPAE | TPSE | FETC_total | FETC_mean |
| --- | --- | --- | --- | --- |
| E | 474.4 | 3795（1 成功） | 3215 | 459.3 |
| F | 484.9 | 3879 | 3268 | 466.9 |
| G | 482.4 | 3859 | 3279 | 468.4 |
| H | 488.1 | 1952.5 | 2714 | 452.3 |
| D | — | — | — | 对照 run 在 `D_v11/` |

---

## 2. 每个任务的运行记录

| 任务 | E | F | G | H | D(v1.1) |
| --- | --- | --- | --- | --- | --- |
| v1_CFD01 | ESR0 (s1✓ s2✗) | 0 | 0 | 0 | ✓ |
| v1_DEL01 | 0 | 0 | 0 | 0 | ✓ |
| v1_DUP01 | 0 | 0 | 0 | 0 | ✗ |
| v1_IRR01 | 0 | 0 | 0 | 0 | ✓ |
| v1_RFS01 | **✓** | 0 | 0 | 0 | ✓ |
| v1_RUR02 | ✗ NO_EDIT | ✗ | ✗ | ✗ | ✗ |
| v1_RUR03 | ✗ | ✗ | ✗ | ✗ | ✗ |
| v1_STM02 | 0 | 0 | 0 | 0 | ✗ |

结构路径：`<arm>/episodes/<task>/vam_coder_v1.2_<arm>/steps/step{1,2}/`  
D：`D_v11/episodes/<task>/vam_coder_v1.1/...`

---

## 3. 每步实际 prompt snapshot

已落盘：每步 `context.txt`、`prompt.txt`、`messages.json`、`result.json`、`response.txt`、`eval_output.txt`。

汇总哈希表：**`p1/results/v1.2_smoke_8tasks/prompt_hashes.csv`**（64 条 E/F/G/H prompt，sha256 + tokens）。

### 3.1 样例（v1_RUR02 step1）

| 臂 | 上下文块 | prompt sha256 前 16 |
| --- | --- | --- |
| E | FILE hot.py + INDEX stable_a/b | `342ae55da49cd5bc`（首轮 buggy run；重跑后见 CSV） |
| F | FILE hot+stable_a+stable_b | 见 CSV |
| G | 全 FILE | 见 CSV |
| H | **仅 FILE hot.py** | 见 CSV |

E 的 RUR02 prompt 含：

```text
--- FILE hot.py (full current source) ---
--- INDEX stable_a.py ---
--- INDEX stable_b.py ---
```

H 无 INDEX 行——符合预注册。

### 3.2 Token 汇总（E/F/G/H）

| 臂 | Σ prompt | Σ completion | Σ Full | Σ Digest | Σ VSO |
| --- | --- | --- | --- | --- | --- |
| E | 3381 | 414 | 15 | **2** | 12 |
| F | 3430 | 449 | 18 | 0 | 11 |
| G | 3428 | 431 | 17 | 0 | 15 |
| H | 3424 | 481 | 15 | 0 | 12 |

E 唯一使用 Digest（RUR02 stable_*）；H 全 0——**配置行为正确**。

---

## 4. O′ 可见性审计

| 臂 | VSO 计数 | 省略事件步 | INSUFFICIENT |
| --- | --- | --- | --- |
| E | 12 | 8（多在 step2） | 0 |
| F | 11 | 8 | 0 |
| G | 15 | 8 | 0 |
| H | 12 | 8 | 0 |

典型：CFD01 step2 省略 invoice+tax；IRR01 step2 省略 alpha（G 还含 beta）。

**严重警告（O′ 跨步语义）**：  
harness 历史只保留 **assistant** 消息；`VisibilityTracker.mark_from_context` 在 step1 装配后记入的哈希 **不在** step2 的 API messages 中。  
结果：step2 可能以“step1 context 曾可见”为由 **省略 must 文件**，模型上下文缺少 FILE 块 → 与 step2 大面积失败（如 CFD01 s2）高度相关。  
这与 V1.0 `history_sent` 问题同源（可见性记账 ≠ 当前 messages）。  
**进入 P1 前必须修复**（跨步 O′ 仅信任 `mark_from_assistant` 或等价 messages 证明）。

---

## 5. Digest 使用情况

- 仅 **E** 产生 DIGEST 行（2 条；RUR02）。  
- F/G/H：0（符合总表）。  
- E vs H：H 上下文更短（RUR02 prompt 无 INDEX）。  
- 1.5B 上 Digest **未**表现为 ESR 优势（E 1/8 vs H 2/8）——**样本过小，不作结论**。

---

## 6. 错误与异常汇总

| 级别 | 项 |
| --- | --- |
| 已修 | `run_p1_v12` 缺 `run_eval` → 已补；buggy 目录保留为 `v1.2_smoke_8tasks_noeval_buggy/` |
| 模型 | 0 HTTP 错误；大量 `NO_EDIT`（协议违例/任务难） |
| **风险** | **O′ 跨步可见性与真实 messages 不一致**（§4） |
| 风险 | V1.2 ESR 冒烟显著低于 D——需在 O′ 修复后重测，不可直接归因架构 |

---

## 7. Git 状态及冻结哈希复核

| 项 | 值 |
| --- | --- |
| HEAD | `155f934bc6c565bd304b2b7438259d592bc348c8` |
| stash | `stash@{0}` 未操作 |
| commit/push/tag | **无** |
| tasks_v1.0.json | `1f3db0090fd62c8f934ed1271b28d0f955c9763fe2956efb30d2a12179f00339` |
| formal_runs.csv | `279d80f8c2a4f9e608395bf891ba91541517193dc7548e9e57dae8bacf9c2375` |
| v1.0 manifest | `e82072f4c222e9927762b383a1e344bcd799d5f08c38486665d7eed8cca696df` |
| prereg（含 d=2 冻结） | `5b1926c17dcd9f12e74f6e29a8ad5983288cfae8c137c2b7d11b50f62339d31b` |

新增：`v1.2_smoke_8tasks/`、`run_p1_v12.py` 修补、既有 `v12/**`。

---

## 8. 最终结论

# PASS WITH WARNINGS

**符合设计的部分**：E/F/G/H 组装、Digest 仅 E、prompt 落盘、eval 接通、无 API 故障、D 对照可跑。

**不建议直接进入正式实验（P1）**，原因：

1. **O′ 跨步可见性实现与“当前 messages 可见”设计意图不一致**（安全性/正确性风险）；  
2. 修复前 E/F/G/H ESR 冒烟远低于 D，结果不可解释；  
3. 需修复后 **重跑** 本 Smoke，再评估是否授权 P1。

**完成等待用户审核；不得自行启动 P1。**
