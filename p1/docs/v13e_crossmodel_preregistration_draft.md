# 预注册补记：V13E(SAH) 跨模型确认性实验（DeepSeek 主批 + Qwen 复现批）

版本：**v1（冻结）**
日期：2026-11-11（起草 / 冻结）
状态：**已冻结。用户书面确认：「先清理一下后台……然后冻结开跑」（2026-11-11，会话原文）。sha256 见 `p1/experiments/v13e_crossmodel/prereg_freeze.json`。冻结先于任何本实验确认性模型请求（含冒烟）。任何修改 = 版本号 +1 + 变更记录。**
与既有预注册关系：除本文件明示差异外，**沿用** `v12f_validation_preregistration.md`（sha `088898a3…`）、`v12f_independent_validation_preregistration.md`（sha `7023da82…`）、`v13b_deepseek_preregistration_draft.md`（sha `cab5381b…`）的解码、成功判定、错误分类、排除、Bootstrap、非劣界口径。

---

## 0. 背景与本实验要回答什么

| 已有证据 | 不得迁移 / 不得主张 |
| --- | --- |
| V12-F P1/P2：prompt −23.6%/−24.2%，O′ −398 tok | 不得记到 V13E 头上 |
| 双 Token B/C：独立贡献未证实（Holm 0.109、非劣 FAIL；且该臂缺 VSO，口径不公） | **禁止**双 Token 主张 |
| DS504（F/CR/ICG，冻结）：ICG −1.4% CI 含 0 | 不得宣称 CR/ICG 有 token 收益 |
| V13E 1.5B 筛选（definitive56，336 集）：SAH −15.6%、ESR 配对差 0.000 | **仅筛选**，不进论文确认性主表 |
| 档位扫描 / 终步修复 / 账本 v1 等负结果 | 进过程与边界披露，不进主张 |

**本实验主问题：**

1. **H-E1（效率，主）**：`vam_coder_v1.3E_SAH` 相对 `vam_coder_v1.2_F` 是否降低 Episode Total Prompt（含 SUMM 摘要器成本的可比口径），且 95% CI 不含 0？
2. **H-E2（能力，主）**：`SAH − F` 的 ESR 配对差 95% CI **下界 ≥ −12pp**（非劣）。
3. **H-E3（外部对照，次级族）**：SAH 与三个外部方法（TRUNC/SUMM/RETR）的 (prompt, ESR) 相对位置——预指定两条主张 + 其余描述（§4.3）。
4. **H-E4（消融，次级）**：`PROJ`（仅 S1）相对 F 的收益与非劣，用于分离 S1/S2 贡献。
5. **跨模型复现（E2）**：上述 H-E1/H-E2 在 **qwen3-coder-flash** 上按同口径复算，判定方向复现（§4.5）。

**明确不做：** ESR 优效主张；跨模型绝对 token 合并；KV/延迟收益；双 Token；改任务集/改评测；事后排除。

---

## 1. 臂定义（冻结 · 7 臂）

| 臂键 | 架构 ID | 机制 |
| --- | --- | --- |
| `MEMORYOFF` | `memory_off` | P1 锚：全仓倾倒、无 O′（沿用） |
| `F`（对照） | `vam_coder_v1.2_F` | V12-F 基座（VSO/O′） |
| `V13EPROJ` | `vam_coder_v1.3E_PROJ` | F + **S1 状态投影**（消融） |
| `V13ESAH`（主） | `vam_coder_v1.3E_SAH` | F + **S1 + S2 义务账本** |
| `TRUNC` | `vam_coder_ext_TRUNC` | 外部 A：滑窗截断（`max_history_chars=1300`） |
| `SUMM` | `vam_coder_ext_SUMM` | 外部 B：LLM 摘要压缩（摘要器 token **全计**） |
| `RETR` | `vam_coder_ext_RETR` | 外部 C：BM25 top-k=3 历史检索（恒留最新） |

**关键配置冻结值：**

| 字段 | 冻结值 | 说明 |
| --- | --- | --- |
| `sah_project_mode` | **`first_last`** | 1.5B 定论批采用档；档位扫描已做（负结果入边界） |
| `sah_ledger`（SAH/ICGSAH） | true（账本 **v2**：窄口径 + 只留未结） | 账本 v1 已废弃 |
| `trunc_budget` | **1300 chars/步** | = definitive56 中 SAH 历史均值 1246 上取整（对齐预算，公平性声明） |
| `hist_summary_recent` | 2 | 摘要器=**同臂同模型同参**（temp=0, max_tokens=180），aux 全入 prompt |
| `hist_retrieve_k` | 3 | 纯 BM25（k1=1.5, b=0.75），保留集按原时序 |
| O′/E/C/must/VSO | 冻结默认，**零修改** | `messages_visibility`/`proof`/`assemble` 不含 SAH 代码（单测护栏） |

**O′ 等价性（预声明机制证据）**：S1 保留集合必含「每路径末版」⇒ 与 `full_files_in_messages` 后写覆盖语义同构；DS504 离线重放 2808 步字段全等 0 失败（`replay_report.json`）+ 单测。本实验**不改**该性质，开跑前复跑离线断言。

**外部臂诚实条款（写入论文）**：TRUNC/SUMM/RETR 为**按文献思想自行实现**（非原作者代码）：截断=现行 `trim_history` 预算档；摘要=同模型压缩器+清洗（防污染可见性提取）；检索=BM25。实现冒烟已过（aux 记账、清洗、选择数、insuf=0）。

---

## 2. 任务集与规模（冻结）

| 项 | 值 |
| --- | --- |
| 任务集 | `p1/tasks_independent_v1/`（48）+ `p1/tasks_independent_v1_dose/`（8）= **56 题**（与 DS504 同题集） |
| 重复 | **R=3** |
| 规模 | 56 × 7 臂 × 3 = **1176 episodes / 模型**；两模型合计 **2352** |
| 随机化 seed | **20261112**（仅乱序，写入 run_meta） |
| Bootstrap | seed=**20261102**，B=10000，cluster=**task_id** |
| 分层 | dose+（8 题）/ dose−（48 题）分层报告；步长 short/medium/long 次级分层 |

---

## 3. 模型与配置（冻结）

| 项 | 主批（E1′） | 复现批（E2） |
| --- | --- | --- |
| 模型 | **`deepseek-v4.1-flash-1017`**（与 DS504 同款） | **`qwen3-coder-flash`** |
| endpoint | 既有 `maas…compatible-mode/v1` | 同 endpoint |
| 鉴权 | `VAM_API_KEY`（不写产物） | 同 |
| 解码 | temperature=0, seed=0, **max_tokens=2048**, history=keep(24000) | **完全相同** |
| 闭包/预算 | d=2, K_max=8, budget=4096, window=8192 | 同 |
| SUMM 摘要器 | 同臂同模型同参（aux 计入 prompt_sum） | 同（=qwen3-coder-flash） |

**代码快照（开跑前逐项写入 run_meta，不一致即停）：**

1. 7 臂 `config.digest()`；
2. 文件 sha：`v12/history_project.py`、`v12/obligations.py`、`v12/hist_external.py`、`v12/config.py`、`v12/messages_visibility.py`、`v12/proof.py`、`v12/assemble.py`、`p1_common.py`、`run_p1_v12.py`；
3. **披露**：`p1_common.build_messages` 相对 P1 冻结 sha（`f0b477b0…`）**已变更**——新增可选参数 `ledger_lines`；默认路径（无账本）**字节等价**由单测断言（`test_v13e_sah.py::TestObligationLedger::test_default_output_byte_identical`）。SYSTEM_PROMPT sha 不变（沿用 `4f591635…`）。

---

## 4. 主假设与判定（冻结）

### 4.1 效率（主）

- **H-E1**：task 级配对 `SAH − F` 的 prompt/episode 均值差 **< 0** 且 95% CI 不含 0（sign-flip 双侧 + Holm，见 §6）。
- 口径：`prompt_sum`（API 计量）**含** SUMM 臂的 aux_prompt_tokens（跨臂可比；aux_completion 单列描述）。

### 4.2 能力（主，非劣 −12pp）

- **H-E2**：`SAH − F` 的 ESR 配对差 95% CI **下界 ≥ −12pp**。

### 4.3 外部对照（次级族，Holm 校正）

预指定两条主张 + 一条描述：

- **H-E3a（对朴素截断）**：`SAH − TRUNC` 的 **ESR** 非劣（CI 下界 ≥ −12pp）——同预算下结构投影不掉能力。
- **H-E3b（对 LLM 摘要）**：`SAH − SUMM` 的 **总成本**（prompt+aux）差 **< 0** 且 CI 不含 0——零 LLM 投影比摘要压缩便宜。
- `SAH − RETR`：**描述性**（表 + CI，不入判定）。

### 4.4 消融与安全

- **H-E4**：`PROJ − F` 报 prompt 差与 ESR 非劣（描述 + 次级判定，不入主族）。
- **安全硬门**（主张臂 F/PROJ/SAH/moff）：**INSUFFICIENT = 0**、DHO = 0、pre_send 违规后仍请求 = 0；出现 architecture 类缺陷 → 停机。
- **外部臂安全**：不设硬门，**如实记录** `pre_send_revised` / `force_full_n` / INSUFFICIENT 并计入其 ESR 与成本（结构破坏型方法的真实代价）。
- **机制门**：SAH/PROJ `sah_folded_blocks` 合计 > 0；SUMM 在 ≥5 步任务上 aux>0；TRUNC 在长任务上发生配对丢弃；RETR 保留数 ≤ k+1。任一机制未触发 → 对应臂标 **机制失败**，其主张不得判支持。

### 4.5 跨模型复现（E2 判定，冻结）

- 主判定**只**来自 DeepSeek 主批；Qwen 批为**复现**：
  - **复现 PASS** = `SAH − F` 方向一致（Δprompt 点估计 < 0）**且** ESR 非劣 PASS（下界 ≥ −12pp）。
  - 复现批**不**与主批合并任何绝对值；两模型分表报告。
- 复现 FAIL（方向反或非劣失败）→ 论文写「跨模型不稳定」，不得只报主批。

### 4.6 多重比较（冻结）

- **主族**（各 1 条，α=0.05，Holm 于族内）：效率 H-E1；非劣 H-E2。
- **次级族**（Holm 校正）：H-E3a、H-E3b、H-E4（prompt 族与 ESR 族分别校正）。
- 分层/难度/Growth/Peak：描述性，不入判定；Growth 标注 ESR 混杂。

---

## 5. 运行与失败分类（沿用 P1）

- 断点续跑 + resume-cleanup；错误分类 protocol/architecture/task/infrastructure；**protocol 计 ESR 失败**；**无事后排除**；infra 整轮失效可重跑并记审计。
- **S5（成本）**：开跑前以 dry-run（每臂 4 集 × 7 臂 = 28 集）估算 ×2 写入 run_meta；粗估主批 ≈ 7M tokens、复现批 ≈ 7M tokens（以 dry 实测为准，超估 2× 即停）。
- **就绪门**：前 36 集若主张臂 ESR 全 0/全 1 或 protocol>20% → 只停不调。
- **冒烟**（dry，不进数据）：每臂 4 集真模型，核对 FILE 协议、usage 字段、SUMM aux>0、TRUNC 丢弃、RETR 保留数、pre_send 无异常。

---

## 6. 统计分析（冻结）

| 项 | 值 |
| --- | --- |
| 单位 | task_id（配对） |
| 检验 | task 级配对 sign-flip（双侧，B=10000） |
| 区间 | task-cluster bootstrap 95% CI（seed 20261102，B=10000） |
| Holm | 主族（H-E1、H-E2 各自族）；次级族（H-E3a/b、H-E4） |
| 非劣 | margin **−12pp**（CI 下界） |
| 分表 | 两模型分表；与 P1/P2/双Token/DS504 **不合并**绝对 token |
| 产物 | `analysis_report.md` + `analysis_verdict.json`（口径与 DS504 一致） |

---

## 7. 执行顺序（全部满足才允许正式请求）

1. 本档 **用户确认 → 冻结 v1**，sha 写入 `p1/experiments/v13e_crossmodel/prereg_freeze.json`
2. 7 臂 config digest + 文件 sha 快照入 run_meta；复跑 O′ 离线等价断言（0 失败）
3. 冒烟 28 集（dry）→ 核对机制门信号与 usage
4. **DS 主批全量 1176 集** → 分析 + 判决（H-E1/E2/E3/E4）
5. **Qwen 复现批 1176 集** → §4.5 复现判定
6. 论文主表 = DS 主批；复现表 = Qwen；1.5B 筛选数据入附录

---

## 8. 诚实条款（写入论文边界）

1. 1.5B definitive56 / 档位扫描 / 修复实验 = **筛选与过程**，不进确认性主表。
2. 双 Token 不进贡献列表；并注明其对照臂缺 VSO 的口径问题（用户 2026-11-11 意见）。
3. 外部三臂为**自行实现的近似**（非原作者代码），只主张「同协议下的相对位置」。
4. 不主张 ESR 优效；只主张效率 + 非劣。
5. 绝对 ESR 可能很低（任务难）——非劣口径与配对差为准，不以绝对值叙事。
6. TRUNC 预算对齐 SAH 均值属**设计选择**（公平性），须披露；预算敏感性（如 1000/1600）**不**在本确认批内做（属探索）。

---

## 9. 冻结核对清单（v1 已勾）

- [x] 7 臂 ID / 配置冻结值（first_last、账本 v2、trunc=1300、SUMM recent=2、RETR k=3）
- [x] 任务集 56 题、R=3、双 seed、两模型解码参数一致
- [x] 主比较 H-E1/H-E2 + 次级族 H-E3a/b/H-E4 + Holm 定义
- [x] 非劣 −12pp；复现判定规则（§4.5）
- [x] 安全硬门（主张臂）与外部臂如实记录口径
- [x] 机制门数值（fold/aux/丢弃/保留数）
- [x] S5 dry×2 规则与粗估（≈7M+7M tokens）
- [x] build_messages sha 变更披露与字节等价单测
- [x] 不做清单（优效/跨模型合并/KV/双Token/事后排除）
- [x] 后台清理核验（无 cron / 无残留进程 / err 日志全空）
- [x] 用户书面「冻结开跑」（2026-11-11）

---

## 10. 变更记录

| 版本 | 日期 | 说明 |
| --- | --- | --- |
| v0.1 | 2026-11-11 | 草稿：7 臂 × 56 题 × 3 × 双模型；外部族与复现判定写入；1.5B E1 于 25/1176 终止并隔离 |
| **v1** | **2026-11-11** | **用户确认「先清理后台…然后冻结开跑」→ 冻结；未发任何本实验确认性请求（含冒烟）** |
