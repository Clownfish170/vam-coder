# VAM-Coder V1.2-r2.1 Smoke（O′ 修复后）总报告

目录：`p1/results/v1.2_smoke_8tasks_opfix/`  
模型：Qwen2.5-Coder-1.5B-Instruct Q6_K；d=2；R=1；8 预注册任务。  
**禁止**据此宣称 V1.2 优于 memory_off 或准确率/效率优势。

---

## 1. 执行摘要

| 项 | 值 |
| --- | --- |
| E/F/G/H 步行 | 64（全部 eval 非空） |
| D v1.1 步行 | 16 |
| 模型/HTTP 错误 | **0** |
| 前置 | HEAD `155f934`；冻结哈希一致；**161 passed**；server `/v1/models` OK |
| 旧 Smoke | **保留** |

---

## 2. ESR / SPR（描述性）

| 臂 | ESR（两步全过） | SPR（步通过） |
| --- | --- | --- |
| D v1.1 | **4/8** | （见 D_v11） |
| E | **3/8** | 8/16 |
| F | 1/8 | 6/16 |
| G | 2/8 | 7/16 |
| H | 2/8 | 7/16 |

修复前 E ESR=1/8；修复后 **3/8**（仍低于 D=4/8，样本极小）。

---

## 3. Token / FETC

| 臂 | TPAE | TPSE | FETC_total | FETC_mean | ΣP | ΣC |
| --- | --- | --- | --- | --- | --- | --- |
| E | 505.9 | 1349 | 2362 | 472.4 | — | — |
| F | 509.8 | 4078 | 3467 | 495.3 | | |
| G | 517.8 | 2071 | 2975 | 495.8 | | |
| H | 509.0 | 2036 | 2881 | 480.2 | | |

（`prompt_hashes.csv` 含逐步 ΣP/ΣC。）

---

## 4. Prefill / cached_tokens（API 口径）

本轮 `request.json` 的 `usage_raw` 中 **未可靠汇总出 cached_tokens**（统计脚本 n=0：字段结构与期望不完全一致）。  
**不得**将 `cached_tokens` 解释为 VAM 真实 KV/显存收益。  
prefill 主报告仍用 **API `prompt_tokens`**（见 per_step / prompt_hashes）。

---

## 5. 协议 / NO_EDIT / INSUFFICIENT

| 项 | E/F/G/H 合计 |
| --- | --- |
| NO_EDIT | **16** |
| INSUFFICIENT | **0** |
| Digest 行（仅 E） | 2 |
| VSO（审计计数） | E6 F6 G7 H8 |

---

## 6. O′ 专项

详见 **`OPRIME_AUDIT.md`**。  

要点：全部省略文件在最终 messages 中有完整 FILE；发送时 pre_send 全 ok；无盲区省略。

---

## 7. 任务覆盖

E/F/G/H：RUR02, RUR03, DEL01, DUP01, CFD01, STM02, RFS01, IRR01 × 2 步。  
D：同任务于 `D_v11/`。

产物：`per_step.csv`、`prompt_hashes.csv`、`episodes/**`、`run_meta.json`、`OPRIME_AUDIT.md`。

---

## 8. Git / 冻结

| 项 | 值 |
| --- | --- |
| HEAD | `155f934…` |
| stash | 未动 |
| tasks / formal / manifest / prereg | 哈希未变 |
| commit/push/tag | **无** |
| 旧 Smoke | 完整 |

---

## 9. 结论

# PASS WITH WARNINGS

- **通过**：修复后 O′ 消息不变量成立；无 API 故障；ESR 相对修复前有改善趋势（E 1→3），但仍 **低于 D**，**不进入 P1**。  
- **警告**：NO_EDIT 仍多；cached 统计不完整；小样本不可推断优势。  

等待用户审核。
