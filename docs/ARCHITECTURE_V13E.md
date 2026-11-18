# ARCHITECTURE_V13E — V13E 旗舰架构（按真实代码恢复）

状态：**ACTIVE · VERIFIED（代码与冻结配置核对）**  
生成：2026-11-18  
正式写法：**V13E**（并用 V1.3E）；项目名 **VAM-Coder**

> 本文只描述**已实现、可核对**的机制。设计稿中的目标若未落地，标 **UNVERIFIED**。

## 1. 定位

V13E = 在 **V1.2F（臂 F）** 选择性交付基座上，增加：

1. **S1** 历史状态投影（`sah_project`）
2. **S2** 义务账本（`sah_ledger`，辅助启发式）

主臂架构 ID：`vam_coder_v1.3E_SAH`（arm `V13ESAH`）  
消融臂：`vam_coder_v1.3E_PROJ`（arm `V13EPROJ`，仅 S1）  
全栈臂：`vam_coder_v1.3E_ICGSAH`（arm `V13ICGSAH`，ICG+S1+S2）

配置定义：`p1/scripts/v12/config.py`（`_ARMS` + `AblationConfig`）

## 2. 模块与依赖（核心 / 辅助）

### 2.1 执行顺序（单步装配）

```text
任务指令 / workspace
    → targets/levels  （E/C/must、FULL/DIGEST/NONE 策略）
    → [若 sah_project] history_project.project_history   ← S1
    → [若 sah_ledger]  obligations 账本行渲染            ← S2（TASK 与 CONTEXT 之间）
    → assemble（v12）+ visibility.safe_omission          ← VP/O′
    → messages_visibility / PreSendCheck
    → 调用模型；usage 落盘 result.json
```

代码锚点：

| 顺序 | 模块 | 路径 | 输入 → 输出 |
| --- | --- | --- | --- |
| 0 | 臂配置 | `v12/config.py` | arm 名 → `AblationConfig`（含 sah_* 开关） |
| 1 | 目标与层级 | `v12/targets.py`, `v12/levels.py` | 任务/图 → E/C/must 与注入级别 |
| 2 | **S1 投影** | `v12/history_project.py` | 历史 messages → 折叠后 history + 统计 |
| 3 | **S2 账本** | `v12/obligations.py` | 历史指令 + workspace → 未结义务行 |
| 4 | **F 交付** | `v12/assemble.py` | 策略 + history → context 文件块/DIGEST |
| 5 | **VP** | `v11/visibility.py` | 可见哈希 → `safe_omission` 允许/拒绝 |
| 6 | 发送前校验 | `v12/messages_visibility.py` | messages → 字段级检查 / INSUFFICIENT |
| 7 | Runner | `run_p1_v12.py` | 装配+调用+审计字段（`n_verified_safe_omissions` 等） |

### 2.2 核心 vs 辅助

| 类别 | 机制 | 说明 |
| --- | --- | --- |
| **核心** | **VP**（O′） | 跨版本保留；V1.1 引入，V1.2F/V13E 默认 `o_prime=True` |
| **核心** | **F** 选择性交付 | V1.2 臂 F：相关非目标 FULL、无关 NONE、task-aware |
| **核心** | **S1** | V13E 主增量；对 VP 提取保持“每路径末版” |
| **辅助** | **S2** | 窄口径未结义务；设计中明确为辅助，防夸大 |
| **对照** | **MOFF** | `MEMORYOFF`，全仓倾倒，非外部 Agent |
| **对照** | TRUNC / SUMM / RETR | 外部历史策略对照臂（`hist_*` 开关） |
| **探索未入核心** | 双 Token、CR/ICG 等 | 见 DEVELOPMENT_HISTORY；非 V13E 核心创新 |

### 2.3 冻结不变量（V13E 默认）

来自 `config.py` 注释与 `load_arm` 默认：

- `o_prime=True`，`edit_target_oprime_forbid=True`，`candidate_full_oprime_forbid=True`
- `exact_targets=True`，`must_full_dep_closure=True`
- `k_max=8`，`closure_depth=2`，`budget_tokens=4096`，`context_window=8192`
- **S1/S2 默认关闭**时，既有臂配置摘要与 V12-F 行为一致（字节级不变意图）

## 3. S1 细节（VERIFIED）

文件：`history_project.py`

- 只处理 `role=assistant` 且匹配 `FILE: path` 围栏块；其余消息原样。
- 保留集合：**每路径末版必留**；mode 可选 `last` / `first_last` / `last2` 等。
- 折叠标记不含 `FILE:` 与围栏，避免被提取正则再次匹配。
- **正确性边界**：对 `full_files_in_messages`（后写覆盖 dict）的提取结果保持 ⇒ VP 候选证明、省略授权、PreSendCheck 字段不变；**不是**任意语义等价。

## 4. S2 细节（VERIFIED，勿夸大）

文件：`obligations.py`（docstring 载明 v2）

- 确定性正则解析，零 LLM。
- add：符号缺席 → 未结；modify：提出后文件哈希未变 → 未结。
- 只渲染未结；一条指令一行；解析失败保守未结但 ≤48 字。
- **边界**：启发式，存在误判/漏判可能；不得写成形式化证明。

## 5. VP 细节（VERIFIED）

文件：`v11/visibility.py`

省略谓词（代码注释原文）：

```text
O′: hash_match ∧ previously_visible_in_messages ∧ file_not_in_current_ctx
    ∧ not_tombstoned_unsafe ∧ not_forced_expand
```

- `VisibilityTracker` 只信任**实际拼进 messages** 的文本。
- `content_sha256`：CRLF→LF、统一尾换行。
- **禁止表述**：VP 发现全部相关文件；VP 消除全部 TOCTOU；`cached_tokens`=KV 显存。

## 6. 与 V1.2F 的差异一览

| 项 | V1.2F (F) | V13E (SAH 主臂) |
| --- | --- | --- |
| 相关非目标 | FULL | FULL（同 F） |
| VP/O′ | 开 | 开（同） |
| S1 | 关 | **开** |
| S2 | 关 | **开**（辅助） |
| 外部对照 TRUNC/SUMM/RETR | — | 可选，非生产臂 |

## 7. 图与伪代码索引

见 `docs/APPENDIX_INDEX.md`（架构图、VP 流程、F+S1 流程、伪代码位置）。
