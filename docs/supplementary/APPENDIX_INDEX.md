# APPENDIX_INDEX — 投稿附录与图料索引

状态：**ACTIVE · 只索引已有材料**  
生成：2026-11-18  
规则：优先索引；**不重复制造不一致副本**；缺证据标 UNVERIFIED。

## 1. 架构与流程图

| 材料 | 位置 | 状态 |
| --- | --- | --- |
| V13E 架构文字版 | `docs/architecture/ARCHITECTURE_V13E.md` | ACTIVE（本次新建） |
| V1.2 架构设计图（文内） | `p1/docs/v1.2/v1.2_architecture_design.md` | ARCHIVE/ACTIVE 混合，以正文版本标注为准 |
| V13E 设计综合 | `p1/docs/v13e_architecture_synthesis.md` | ACTIVE 草稿 |
| 版本演进 | `docs/development-history/DEVELOPMENT_HISTORY.md` | ACTIVE |
| VP/O′ 流程 | `docs/mechanisms/MECHANISM_VISIBILITY_PROOF.md` + `v11/visibility.py` | ACTIVE |
| F+S1 流程 | `ARCHITECTURE_V13E.md` §2 执行顺序 | ACTIVE |

> 若需位图：`v06_figs/` 为论文曲线图，**不是**架构框图；架构框图若无现成 PNG，可从本文 SVG/描述重绘（重绘稿另存，不覆盖历史）。

## 2. 数学定义与符号

| 内容 | 位置 |
| --- | --- |
| 集合 E/C/M/F、RSR 等 | `p1/docs/v1.2/v1.2_method_formulation.md` |
| O′ 谓词 | `v11/visibility.py` docstring；MECHANISM 文档 |
| S1/S2 规则 | `history_project.py`, `obligations.py` docstring |

## 3. 关键算法伪代码

| 算法 | 来源 |
| --- | --- |
| VP safe_omission | `visibility.py` 函数体（可摘为伪代码） |
| assemble 主循环 | `v12/assemble.py` |
| S1 project_history | `history_project.py` |
| S2 parse/render | `obligations.py` |

## 4. 任务与配置表

见 `docs/methodology/EXPERIMENT_INDEX.md` §4–6。

## 5. 统计与故障注入

| 材料 | 路径 |
| --- | --- |
| 统计口径（V12F） | `V12F_final_validation_and_submission_report.md` §1.3 |
| 成本/统计（Transfer） | `STATS_AND_COST_P1_SWEBENCH.md`；实验目录内 `STATS_AND_COST.md` |
| VSO 注入 | `vso_fault_injection/*report*` |
| 稳健性 | `V13E_CLUSTER_ROBUSTNESS_AUDIT.md` |

## 6. 双 Token 取舍

| 材料 | 状态 |
| --- | --- |
| 补记 v1 | SUPERSEDED（由 v2 取代任务集条款） |
| 补记 v2 | ACTIVE 历史补记 |
| 实验报告 | `dualtoken_ablation/dualtoken_report.md` — **不支持**独立贡献 |

## 7. 局限性（写作时必须保留）

来自 V12F 未解决问题与 Transfer 诚实边界：

1. 双 Token 独立贡献未证实  
2. KV 显存无实测  
3. P1 任务集族依赖 / 有效独立设计披露  
4. Transfer 非官方 SWE-bench 协议  
5. S2 启发式误判风险  
6. VP 边界（非全文件发现、非全部 TOCTOU 消除）

## 8. 手稿与插图（工作区顶层，未入 git 主树）

| 文件 | 说明 |
| --- | --- |
| `论文草稿_v0.6_正式稿.md/.docx` | 手稿 |
| `论文草稿_v0.6_插图版.docx` | 插图版 |
| `V13E_MANUSCRIPT_REVISION_v0.6.md` | 修订说明 |
| `V13E_v0.5_readonly_evidence_audit.md` | 只读证据审计 |
| `v06_figs/fig4–fig9*.png` | 曲线/森林图等 |
| `V13E_PROJECT_ARCHIVE.zip` | 项目归档包（大文件） |

顶层路径**未强制迁入** repo（引用关系未完全核验）→ 见清理报告。
