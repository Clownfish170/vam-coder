# VAM-Coder V1.2-r2.2 P1 正式实验执行报告

状态：**P1 执行完成**（用户已授权）。  
目录：`p1/experiments/v12_p1_execution/`

---

## 1. 执行摘要

| 项 | 值 |
| --- | --- |
| 计划 Episode | **504**（24×7×R3） |
| 完成 | **504 / 504**（fail=0） |
| 步 / 结果 | **1008** result.json |
| 实际模型请求 | **1008**（prompt_tokens 全 >0） |
| 随机化 | seed **20261102**，504 唯一 |
| Workspace pre/post/diff | **504 / 504 / 504** |
| 起止 | 约 2026-11-02 05:23 → 05:50 UTC |
| 模型 | Q6_K @ llama-server 8192 / parallel=1 |

---

## 2. 配置（按预注册，未改）

24 tasks · arms **A,B,D,E,F,G,H** · R=3 · seed/temp/max_tokens=0/0/1024 · history=keep · d=2 · Kmax=8。

随机化：`randomization_manifest.json`（独立于 P0）。

---

## 3. 主结果（描述性；非显著性结论）

### ESR（两步全过 / 72）

| 臂 | ESR | SPR(/144) | TPAE | TPSE | FETC_total | FETC_mean |
| --- | --- | --- | --- | --- | --- | --- |
| A memory_off | 34/72 | 90 | 635.9 | 1346.6 | 23496 | 618.3 |
| B symbol_full | 29/72 | 83 | 646.5 | 1605.1 | 27316 | 635.3 |
| D v1.1 | 30/72 | 84 | 617.8 | 1482.6 | 24933 | 593.6 |
| **E v1.2** | **32/72** | 84 | **579.3** | **1303.4** | 21696 | 542.4 |
| F | 35/72 | 87 | 584.0 | **1201.4** | 20229 | 546.7 |
| G | 34/72 | 94 | 596.7 | 1263.5 | 21932 | 577.2 |
| H | 31/72 | 85 | **573.3** | 1331.6 | 22136 | 539.9 |

**门禁点估计（对照预注册，仅供参考，须 CI/配对分析后解释）**：

| 比较 | 观察 |
| --- | --- |
| E vs D ESR | 32 vs 30 → 点估计不劣于 D−0.10 |
| E vs A ESR | 32 vs 34 → 差 2/72≈2.8pp（在 A−0.15 内） |
| E TPSE vs D | 1303 vs 1483 → **更低** |
| E TPSE vs A | 1303 vs 1347 → **略低** |
| E TPAE vs A | 579 vs 636 → 更低 |

**禁止**据此写“显著优于/证明有效/已证非劣”；须补 Wilson CI 与 task-cluster bootstrap（prereg §7）。

明细：`per_step_all.csv`、`summary_by_arm.csv`、各 `runs/<ep>/runner_out/`。

---

## 4. Workspace 证据链

| 文件 | 数量 |
| --- | --- |
| `workspace_pre_manifest.json` | **504** |
| `workspace_post_manifest.json` | **504** |
| `workspace_diff.json` | **504** |

实现：`p1/scripts/v12/workspace_audit.py` + orchestrator（pre=冻结源项目哈希，post=episode workspace）。

---

## 5. 完整性与 Git

| 项 | 结果 |
| --- | --- |
| HEAD | `155f934bc6c565bd304b2b7438259d592bc348c8` |
| stash@{0} | 未动 |
| V1.0 三项 SHA | **未变** |
| 覆盖 P0/正式数据 | **否**（独立 `v12_p1_execution/`） |
| 无自动重试刷成功 | **是**（rc=0 一次通过） |

### 执行注记

- A/B 臂子进程 stdout 曾出现 **GBK 解码线程警告**（UnicodeDecodeError），**不影响 returncode=0**；结果文件完整（A/B 各 144 步）。  
- 可选后续：orchestrator 用 `encoding="utf-8", errors="replace"` 读 stdout（非阻断）。

---

## 6. 数据采集字段（v1.2 臂）

- context / messages / pre_send_check / injection_audit / response / eval / result  
- workspace pre/post/diff  
- 失败分类可后处理（同 P0 方法）

---

## 7. 局限

- 单模型 1.5B；任务级 NO_EDIT/推理噪声仍在  
- 本报告为 **执行完成摘要**，非统计终稿  
- VP/vproof：O′ 语义边界见 method（不保证语义完全等价）

---

## 8. 结论

# P1 EXECUTION COMPLETE

- 504/504 episodes，1008 请求，0 硬失败  
- 随机化与 workspace 证据链完整  
- 冻结资产未变  

**下一步建议（需你决定）**：按 prereg 做 CI/bootstrap/门禁判定与失败归因终稿；**本报告不自动进入论文结论或新实验。**
