# P1 Execution Readiness Gate 报告

性质：**只读门禁 + 隔离自测**。目录 `p1/experiments/v12_p1_readiness/`。  
未改正式代码/预注册/任务；未跑真实模型/P1。

---

## Overall Readiness

# CONDITIONAL PASS

| # | 维度 | 判定 |
| --- | --- | --- |
| 1 | Git Integrity | **PASS** |
| 2 | Frozen Asset Integrity | **PASS** |
| 3 | Workspace SHA Readiness | **CONDITIONAL**（方案自测 PASS；**尚未接入**正式 runner） |
| 4 | Safety Integration Readiness | **PASS**（Mock/单测；非真实模型） |
| 5 | Experiment Configuration Readiness | **PASS**（与预注册一致；server 当前未响应 → 见资源） |
| 6 | Statistical Logging Readiness | **CONDITIONAL**（字段可从现有 result/psc 扩展；缺 pre/post manifest 落盘） |
| 7 | Resource Readiness | **CONDITIONAL**（磁盘 OK；**llama-server 本门禁时未探测到**） |

---

## 1. 冻结状态

| 项 | 结果 |
| --- | --- |
| Branch `p1/v1.1` / HEAD `155f934…` | **PASS** |
| stash@{0} | **PASS**（存在未动） |
| V1.0 三项 + 七份 r2.2 文档 SHA | **全部 PASS** |
| M1–M4 / M3-FIX-01 文件存在 | **PASS** |
| P0/post_review/P1 review 资产存在 | **PASS** |
| `pytest p1/tests tests` | **181 passed** |
| `test_v12_m3_fix01_gate` | **10 passed** |

---

## 2. Workspace SHA（阶段二）

- **正式 runner 尚未**在 P1 episode 写 `workspace_pre/post_manifest` → **未接入**  
- 隔离自测 `_ws_sha_selftest.py` → `workspace_sha_test_result.json` **全部 True**  
- 设计见 `workspace_sha_design.md`（字段/时序/diff 分类）

**Workspace SHA Readiness：CONDITIONAL** — 方案可复现，**缺 P1 执行器挂钩**（需另行授权改 runner，本轮不改）。

---

## 3. VP / INSUFFICIENT 安全门禁（阶段三）

| 测试 | 来源 | 结果 |
| --- | --- | --- |
| T1 正常允许 | 单测 `m3_fix01` pass 路径 | **PASS** |
| T2 缺 must → 0 调用 | `test_integration_missing_required_chat_zero` | **PASS** |
| T3 verify 失败 → 0 | `test_integration_second_fail` | **PASS** |
| T4 E 验证失败 → 0 | `test_integration_edit_target_fail` | **PASS** |
| T5 C 失败 → 0 | `test_integration_candidate_fail` | **PASS** |
| T6/T7 force 后仍失败 → 0 | 同上二次失败 | **PASS** |
| T8 正常 n=2 | pass / recover 测试 | **PASS** |
| messages ≡ pre_send | `test_v12_oprime_messages` + r2.2 | **PASS** |

**性质**：Unit + **Mock 集成**；**不是**真实模型实验。  
**INSUFFICIENT live 触发**：仍 **NOT_VERIFIABLE**（P0 为 0）。

详见 `safety_integration_test_report.md`。

---

## 4. 实验配置（阶段四）

| 项 | 预注册 | 实测 | 结果 |
| --- | --- | --- | --- |
| 模型 Q6_K | 是 | 文件在（P0 用过） | **PASS** |
| ctx 8192 / parallel 1 | 是 | P0 时一致 | **PASS**（历史） |
| seed/temp/max_tokens | 0/0/1024 | runner 默认 | **PASS** |
| history keep | keep | 执行参数 | **PASS** |
| d=2 Kmax=8 | 是 | config | **PASS** |
| 24 任务 / 7 臂 / R=3 | 是 | prereg§4 | **PASS** |
| ≈1008 请求 | 是 | resource | **PASS** |
| 本门禁时 `/v1/models` | 应可用 | **超时无响应** | **WARNING** |

---

## 5. 统计与日志（阶段五）

| 字段 | 现状 |
| --- | --- |
| episode/task/arm/rep/step/eval/tokens | result.csv **有** |
| EditTargets/must/insufficient | result **有** |
| pre_send / VP(vproof) | pre_send_check **有** |
| raw response / eval_output | **有** |
| workspace pre/post/diff | **缺** → CONDITIONAL |
| ESR/SPR/TPAE/TPSE/FETC | 可从 per_step 重算（P0 已证） |
| 95% CI / task bootstrap | 预注册有；**执行器未内置** → 分析阶段脚本 |
| 零成功/零失败 | 定义在 method/prereg；**OK** |
| 重试计数 | 预注册累计 API token；runner 无自动重试 **OK** |
| cached_tokens | 可记；禁当 KV 节省 **OK** |

---

## 6. 资源（阶段六）

| 项 | 结果 |
| --- | --- |
| 磁盘 D: free | **~34 GB** PASS |
| 日志量级 | ~504 eps → 数十–百 MB PASS |
| server 本门禁时 | **未响应** WARNING（P0 曾可用；P1 前须再起） |
| 串行 1008 | 估 1–4h PASS（计划） |
| 并行污染 | 规范禁止并行多实验 PASS |
| 中断/重试计数 | 预注册有规则；执行器无 auto-retry **PASS** |

见 `resource_final_check.md`。

---

## 7. P1 Authorization Recommendation

# READY FOR USER AUTHORIZATION

**含义**：技术准备达到 **授权评审** 条件。  
**不等于** 获得 P1 执行授权。

### 授权前建议关闭的 WARNING（非代码 BLOCKER）

1. P1 启动前确认 **llama-server** 健康（本门禁时 down）。  
2. 执行器接入 **workspace pre/post manifest**（需你授权改 runner，或接受仅目录级隔离+源快照 hash）。  
3. 报告模板使用 **VP/vproof**（非 O′ 作为正式名）。

---

## 交付清单

1. `p1_execution_readiness_report.md`  
2. `workspace_sha_design.md`  
3. `safety_integration_test_report.md`  
4. `p1_execution_checklist.md`  
5. `p1_blocker_register.csv`  
6. `resource_final_check.md`  
7. `git_integrity_report.md`  

等待你审阅。**不启动 P1。**
