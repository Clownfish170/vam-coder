# DEVELOPMENT_HISTORY — V1.0 → V1.1 → V1.2F → V1.3E

状态：**ACTIVE · 索引型（细节以各版本文档与提交为准）**  
生成：2026-11-18  
原则：**只梳理真实演进**；不虚构功能/提交/结果；目标≠实现，预期≠结果。

## 0. 版本主轴

```text
V1.0 初始架构
  → V1.1 可验证架构（VP/O′）
    → V1.2F 成熟版本（臂 F 选择性交付 + 编辑安全 r2.2）
      → V13E 最终旗舰（F + S1 + 辅助 S2）
```

双 Token、CR/ICG/VAD 等为**探索支线**，见 §4。

## 1. V1.0 — 初始架构

| 项 | 内容 |
| --- | --- |
| 设计目标 | 可运行的编码记忆/装配原型与任务集 |
| 原有不足 | `history_sent` 与当前 messages 不一致（后续 V1.1 文档明确） |
| 主要文档 | `p1/docs/v1.0/`（canonical；指针 `docs/history/V1.0/`） |
| 冻结记录 | `p1/results/freeze_v1_0.md`；manifest `p1/manifests/p1_v1.0_manifest_*.json` |
| 代码 | `p1/scripts/run_p1.py`（早期 runner） |
| 遗留影响 | 可见性记账缺陷 → V1.1 必须引入 VP |

状态标记：ARCHIVE（过程基线，保留）

## 2. V1.1 — 可验证架构

| 项 | 内容 |
| --- | --- |
| 设计目标 | 修复可见性；可审计的安全省略 |
| 机制增改 | **新增 VP/O′**（`VisibilityTracker` + `safe_omission`）；assemble 接入 |
| 变化原因 | V1.0 全局记账不可信 |
| 代码 | `p1/scripts/v11/`（visibility/assemble/controller…） |
| 文档 | `p1/docs/v1.1/v1.1_architecture_design.md` 等 |
| 实验 | `p1/results/v1.1_validation_report.md` |
| 遗留 | 仍需更细的非目标策略与编辑安全 → V1.2 |

状态标记：ACTIVE（机制层仍被 V13E 复用）

## 3. V1.2 / V1.2F — 成熟版本

| 项 | 内容 |
| --- | --- |
| 设计目标 | 任务感知选择性交付 + 编辑目标安全 |
| 机制 | 臂 E/F/G/H；**F = 相关非目标 FULL**；r2.2：E/C 禁 O′、CandidateFull、分列 verified |
| 关键文档 | `p1/docs/v1.2/v1.2_architecture_design.md`, `v1.2_method_formulation.md`, `v1.2_experiment_preregistration.md`（根路径冻结） |
| 代码 | `p1/scripts/v12/`（assemble/levels/targets/config…） |
| 实验 | P1/P2/P3-A；报告见 `experiments/V12-F/reports/V12F_final_validation_and_submission_report.md` |
| 结果口径 | P1 prompt −23.6%/−24.2%，ESR 非劣 PASS；P2 中 O′ 主导 −398 tok/集（见总报告 §1.4） |
| 遗留 | 历史多版本膨胀、“要求蒸发” → V13E S1/S2 |

状态标记：ACTIVE（F 为 V13E 基座）

## 4. 探索支线（非最终核心创新）

| 支线 | 文档/实验 | 结论摘要 | 论文定位 |
| --- | --- | --- | --- |
| **双 Token** | `v12f_validation_preregistration_addendum_dualtoken*.md`（v2 取代 v1 任务集条款）；`experiments/dualtoken_ablation/` | H-B/H-C **不支持**；独立贡献未证实 | **探索过程**；A−D 收益归 VP/选择性交付，不归双 Token |
| CR / ICG / OSCA | `v13a_*`, `v13b_*` 设计与筛选 | 筛选/迭代材料 | 边界与消融素材，非 V13E 主叙事 |
| VAD 慢层 | `v13c_distillation_design.md`, `v13d_preview/` | 预览级 | 不写成已证实主贡献 |
| DeepSeek 扩展预注册 | `v13b_deepseek_preregistration_draft.md` | 草稿 | 与主实验分表 |

状态标记：ARCHIVE / SUPERSEDED（按各文件自身标记）

## 5. V13E — 最终旗舰

| 项 | 内容 |
| --- | --- |
| 设计目标 | 在不改 VP/F 语义下压缩历史多版本 + 防指令蒸发 |
| 机制 | **S1** 投影（核心增量）、**S2** 账本（辅助）；基座 F+VP |
| 设计文档 | `v13e_sah_design.md`, `v13e_architecture_synthesis.md`, `v13e_crossmodel_preregistration_draft.md` |
| 代码 | `history_project.py`, `obligations.py`；臂 `V13EPROJ`/`V13ESAH`/`V13ICGSAH` |
| 主实验 | 双模型 crossmodel；**56** repository-editing 合成任务（`v13e_sah/definitive56*`） |
| 扩展 | P1_TRANSFER / SWE-bench Lite 10 实例（**不取代**主实验） |
| 规范架构说明 | `docs/ARCHITECTURE_V13E.md` |

状态标记：ACTIVE（旗舰）

## 6. 命名与映射（新文档）

- O′ → **VP**（见 `docs/GLOSSARY.md`）
- 历史文件**不改名**；SUPERSEDED 关系写在本索引与 dualtoken v2 文档内
