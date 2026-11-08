# V1.2-r2.2 P0 Smoke 最终报告（阶段 C）

状态：**真实模型 Smoke 完成**。目录 `p1/experiments/v12_p0_smoke/execution/`。  
**不是** P1；**不作**统计显著性或架构有效结论。

---

## 1. 目的与环境

| 项 | 值 |
| --- | --- |
| 目的 | 验证 M1–M4 / M3-FIX-01 真实模型链路 |
| 模型 | qwen2.5-coder-1.5b-instruct-q6_k |
| server | llama-server :8080，ctx=8192，parallel=1 |
| seed/temp/max_tokens | 0 / 0 / 1024 |
| history | keep |
| d=2 / Kmax | 2 / 8 |

---

## 2. 执行规模

| 指标 | 值 |
| --- | --- |
| 计划 Episode | **32**（8×4×R1） |
| 开始 / 完成 | **32 / 32** |
| 随机序 seed | **20261102**（与阶段 B 一致） |
| 实际模型请求 | **64**（=32×2，全部 prompt_tokens>0） |
| 阻断请求 INSUFFICIENT | **0** |
| 自动重试 | **0** |

---

## 3. 成功与失败

| 臂 | ESR（8） | SPR（/16） | TPAE | TPSE | FETC_total | FETC_mean |
| --- | --- | --- | --- | --- | --- | --- |
| **E** | **4/8** | 9 | 539.4 | 1078.8 | 2026 | 506.5 |
| **F** | 3/8 | 8 | 542.1 | 1445.7 | 2599 | 519.8 |
| **G** | 4/8 | 9 | 556.5 | 1113.0 | 2089 | 522.2 |
| **H** | 4/8 | 9 | 542.5 | 1085.0 | 2013 | 503.2 |

- 零成功臂：无（各臂均有成功）→ TPSE 有限值  
- Prefill：主指标 API `prompt_tokens`；`cached_tokens` 若有仅作服务端前缀缓存，**不作** KV 节省主张  

明细：`summary.csv`、`per_step_all.csv`。

---

## 4. 策略行为抽查（RUR02 step1）

| 臂 | 上下文 | 符合 r2.2 |
| --- | --- | --- |
| E | hot FULL + **INDEX** stable_* | 是 |
| F | hot + stable **全 FULL** | 是 |
| G | 全 FULL（无 task-aware 过滤） | 是 |
| H | **仅 hot FULL** | 是 |

EditTargets（hot）各臂均 FULL。

---

## 5. IRR01 专项（文件覆盖）

| 检查 | E/step2 |
| --- | --- |
| 当前 context 含 `alpha.py` FULL | **是** |
| `edit_target_full_verified` | **true** |
| workspace `alpha.py` | **`a()` 保留 + `a2()`** |

**覆盖风险已消除（相对 r2.1 旧失败形态）。**

---

## 6. EditTarget / O′ / 协议

| 项 | 结果 |
| --- | --- |
| E/C 强制 FULL | 验证链路生效；0 次 INSUFFICIENT 阻断 |
| O′ 误省必须文件 | **未观察到**（结合 pre_send ok） |
| 协议违规（非 FILE/NO_EDIT） | 以 per_step / response 为准；错误列 64 步空 |
| 请求前阻断 | 本轮无触发；门闩仍由单测覆盖 |

---

## 7. 失败分类（ESR 未满 8/8 的部分）

以各臂 4 个失败 episode 为主：模型 NO_EDIT / 推理错误（RUR03/STM02 等），属 **模型能力边界**，非请求前阻断失效。  
详见 `summary.csv` 与各 `episodes/*/steps/*/eval_output.txt`。

---

## 8. 工作区隔离

- 每 Episode 独立 `episodes/<task>/<arm>/workspace`（runner copytree）  
- 无跨 Arm 继承  
- 初始源：冻结 `p1/tasks/<id>/project`  

**PASS**（结构隔离；未另做全目录哈希对账表——可按需补 `workspace_manifest/`）

---

## 9. 冻结与 Git（执行后）

| 项 | 值 |
| --- | --- |
| HEAD | `155f934…` |
| V1.0 三项哈希 | **未变** |
| r2.2 文档 | **未改**（执行只写 execution/） |
| stash | `stash@{0}` 未动 |
| commit | **无** |

---

## 10. 未覆盖 / 未做

- CandidateFull 高召回（按审查保留保守策略）  
- 显著性、非劣、P1 门禁  
- D arm  
- R=3  

---

## 11. 是否建议进入 P1

# CONDITIONAL PASS

**依据**：32/32 完成、64 请求、策略分层正确、IRR01 alpha 全文保留、0 阻断违规、冻结未破。

**条件（进入 P1 评审前建议）**：

1. 人工审阅 `summary.csv` 与失败 episode 原始 eval；  
2. 确认无需再改 r2.2 安全规则；  
3. P1 仍须 **单独授权**（预注册门禁 + 更大样本）。  

**P0 PASS ≠ P1 自动授权。**
