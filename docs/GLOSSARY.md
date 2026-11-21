# GLOSSARY — VAM-Coder 术语表（V13E）

状态：**新建规范文档（VERIFIED 映射，不改历史原文）**  
生成：2026-11-18 · 适用：新文档、论文写作、代码注释  
规则：旧名 **O′** 只在本表与新文档中建立映射；**禁止修改**预注册、run_meta、冻结日志中的原始写法。

## 1. 项目与版本

| 正式写法 | 含义 | 历史/别名 | 证据 |
| --- | --- | --- | --- |
| **VAM-Coder** | 项目名（统一大小写与连字符） | vam_coder（代码/架构 ID 前缀）、VAM Coder | `README.md`、`src/vam_coder/`、架构 ID `vam_coder_v1.2_F` 等 |
| **V13E**（正式首选；**V1.3E** 可并用） | 最终旗舰架构版本 | V1.3E、v13e、V13E·SAH | `p1/docs/v13e_*.md`、`run_p1_v12.py` 臂 `V13ESAH`/`V13EPROJ` |
| **V1.2F** | 成熟基线（arm F） | V12-F、vam_coder_v1.2_F | `p1/scripts/v12/config.py` 臂 `F`；V12F 报告 |
| **V1.1** | 可验证架构（引入 O′/VP） | v1.1、V1.1.1 | `p1/docs/v1.1/`、`p1/scripts/v11/` |
| **V1.0** | 初始架构 | v1.0、P1 v1.0 | `p1/docs/v1.0/`、`p1/results/freeze_v1_0.md` |

## 2. 核心机制

| 正式写法 | 全称 | 代码位置 | 历史旧名 | 边界（勿夸大） |
| --- | --- | --- | --- | --- |
| **VP** | Visibility Proof（可见性证明） | `p1/scripts/v11/visibility.py`（`VisibilityProof`/`VisibilityTracker`/`safe_omission`） | **O′**（省略谓词/可见性省略） | 只证明**当前 messages 中仍可见**的内容哈希匹配；**不**声称发现全部相关文件，**不**消除全部 TOCTOU |
| **F** | Selective Context Delivery（选择性上下文交付） | `p1/scripts/v12/assemble.py` + 臂 `F`（`non_target_related=full`） | V1.2 臂 F、VSO/O′ 选择性交付 | 相关非目标 FULL、无关 NONE、must/ET 等约束见 `levels.py`/`targets.py` |
| **S1** | Verified History Projection（已验证历史投影） | `p1/scripts/v12/history_project.py`（`project_history`） | SAH project、状态投影、历史折叠 | 按路径折叠历史 FILE 块；对 VP/O′ 提取语义保持末版 ⇒ **投影等价**，非“语义等价”全称 |
| **S2** | 义务账本（辅助启发式） | `p1/scripts/v12/obligations.py` | SAH ledger、S2 ledger | **辅助启发式**，窄口径+只留未结；**不**夸大为独立核心创新 |
| **MOFF** | Memory Off（全量仓库上下文管理策略） | 臂 `MEMORYOFF`，`assemble_memory_off` | memory_off、全仓倾倒基线 | **不是外部 Coding Agent**；是本仓对照的上下文策略 |

## 3. 安全与交付谓词

| 正式写法 | 含义 | 证据 |
| --- | --- | --- |
| **PreSendCheck / 发送前验证** | 组装后、调用模型前的完整性/可见性校验 | `messages_visibility.py`、`p1_common.py` |
| **fail-closed** | 校验失败则不发送模型请求，记 INSUFFICIENT 等 | dualtoken 报告、VSO 设计 |
| **must / ET / E / C** | 必须全文、编辑目标、候选全文等集合 | `targets.py`、`v1.2_method_formulation.md` |
| **ESR** | Episode Success Rate（任务级成功口径，以预注册为准） | 预注册与各实验报告 |
| **cached_tokens** | API usage 中的缓存 token 计数 | `result.json` usage 字段 |
| **禁止** | 将 `cached_tokens` 解释为 **KV 显存** | 无实测证据（V12F 报告未解决问题 #3） |

## 4. 实验与扩展

| 正式写法 | 含义 | 边界 |
| --- | --- | --- |
| **P1_TRANSFER** | 真外部 SWE-bench Lite 10 实例扩展验证 | **不得取代** V13E 主实验（56 合成题）定位；非官方 leaderboard |
| **双 Token / Dual-Token** | 符号寻址 / 静态表示+符号 ID 探索 | **探索过程**，非最终核心创新；独立贡献**未证实** |
| **VSO** | 可见性安全省略相关故障注入与校验体系 | 见 `vso_fault_injection_evaluation_design.md` |
| **本地重实现基线** | 为对照在本仓实现的外部方法近似 | **不得**称为原作者官方实现 |
