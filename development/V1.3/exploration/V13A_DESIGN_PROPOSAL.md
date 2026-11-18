# VAM-Coder v1.3A 研究与架构设计提案

状态：**设计定稿（单文件交付）**  
日期：2026-11-07  
基础：V12-F（`vam_coder_v1.2_F`）已验证机制  
交付物：本文件（`V13A_DESIGN_PROPOSAL.md`），不附带其他设计文档

---

## 0. 摘要

v1.3A 不是对 v1.2-F 的参数微调，也不是对旧双 Token 实验（B/C 臂）的复刻，而是一次**以降低上下文增长率为第一优先级**的机制重设计。

主方案定为 **CR-Memory（Content–Reference Memory）**：

- **C（Content Unit）**：外部存储中规范化、内容寻址、可追溯的记忆内容单元；
- **R（Reference）**：指向 C 的符号引用（ID、版本钉扎、读取范围、依赖）；
- **Resolver**：发送前的确定性展开与完整性验证器——模型**永远不会**只收到一个无法解释的裸 ID。

效率收益不来自“把正文换成短 ID”，而来自：内容一次存储、多轮/多任务复用；已可见内容走既有 O′ 省略；未必需要全文的相关内容以**可读的紧凑 C 形式**交付；一切无法证明安全的情形 fail-closed 回退到 V12-F 全文路径。

**明确判定**：不需要训练新 tokenizer，也不需要两个 special token。C/R 是**两种逻辑表示角色**（外部内容对象 vs 引用对象），在 Prompt 中最多表现为一种统一的 `MEM` 文本标记 + 展开正文。若本地实验显示“单 ID + 紧凑正文”与 CR 等效，则应放弃“双 Token”命名，只保留单标记机制——本文 §9 给出该裁决规则。

**命名冲突警示**：现有代码中臂名 `V13A` / `vam_coder_v1.3_V13A` 指的是 V1.3-M1 的 `adaptive_a` 相关文件策略（`p1/scripts/v12/config.py` `_ARMS["V13A"]`），与本提案的“v1.3A 双表示机制”**不是同一对象**。本版本架构标识建议使用 `vam_coder_v1.3A_CR`，禁止复用 `vam_coder_v1.3_V13A`。

---

## 1. 现有代码与历史实验审计

审计方式：直接读取源码、预注册、实验报告与原始 CSV/JSON；对重要结论给出文件路径与符号名。无法验证的项单独标明。

### 1.1 项目真实结构（已实现 vs 仅文档）

| 层级 | 路径 | 状态 |
| --- | --- | --- |
| P0 符号索引/失效/路由原型 | `src/vam_coder/{parser,store,invalidation,router,pipeline}.py` | **已实现**（86 tests） |
| V1.1 可见性/控制器 | `p1/scripts/v11/` | **已实现** |
| V1.2 装配与安全门 | `p1/scripts/v12/{levels,assemble,targets,proof,messages_visibility,config}.py` | **已实现** |
| V1.2 主 runner | `p1/scripts/run_p1_v12.py` | **已实现** |
| 消息/模型客户端 | `p1/scripts/p1_common.py`（`SYSTEM_PROMPT`、`build_messages`、`chat_completion`、`trim_history`） | **已实现** |
| 自适应 related 策略（旧名 V13A） | `p1/scripts/v12/adaptive_features.py` + `config._ARMS["V13A"]` | **已实现**；holdout 已跑，结论偏负 |
| V13B no-body→NONE | `config._ARMS["V13B"]` + `levels.build_plan` 分支 | **已实现**；P2/round2 判定**放弃** |
| 旧双 Token（B/C） | `p1/experiments/dualtoken_ablation/dualtoken_strategies.py`（monkeypatch） | **仅实验侧包装**；生产代码零修改 |
| Memory Resolver（CR 层） | — | **未实现**（本提案对象） |
| 跨 Episode 持久记忆库 | — | **未实现**（P0 store 每 episode 重建，见下） |
| 独立任务集确认性实验 | `p1/experiments/independent_validation/` | **未完成**（审计时 `execution_log.jsonl` 仅 24/720 行） |

### 1.2 V12-F 已验证机制（保留，不重写）

以下机制有预注册 + 确认性数据 + 安全专项支撑，v1.3A **原则上原样保留**：

1. **任务感知选择性交付**：`build_plan`（`levels.py`）产出 `ExpandPlan`，层级 `FULL | DIGEST | NONE`；集合约束 \(E\cap C=\varnothing\)，\(E\cup C\subseteq F\)，\(E\subseteq M\)（`docs/v1.2_method_formulation.md` §1.1/§3）。
2. **编辑目标完整性**：`parse_edit_targets`（`targets.py`）；E/C 强制 FULL、禁 O′；发送前 `verify_omissions_in_messages`（`messages_visibility.py`）分列 `edit_target_full_verified` / `candidate_full_verified`。
3. **O′/VSO 可见性语义**：候选证明仅来自将进入本步的历史（`proof.tracker_from_history`）；**最终授权**来自最终 messages 中完整 FILE + SHA256=磁盘（`messages_visibility.verify_omissions_in_messages`）。历史 assistant 中 FILE **不得**代替本轮 E/C 的 FULL。
4. **must_full 依赖闭包**：`dependency_closure`（`levels.py`），depth=2 冻结。
5. **安全失败回退**：`should_call_model`（`run_p1_v12.py`）在 INSUFFICIENT 或 pre_send 失败时**禁止**模型请求；修订一轮后仍失败 → 记 `EDIT_TARGET_FULL_VERIFY_FAIL` 等并跳发。
6. **Token 计量**：API `prompt_tokens`（含 system + 全部历史 + 本步 instruction/context 等最终 messages 全文）；`cached_tokens` 单列为服务端前缀缓存，**禁止**解释为 KV 显存收益（`p1_common.chat_completion`、V13 holdout 报告 §1）。

**历史消息累积规则（关键事实）**：`run_p1_v12.py` 每步仅 `history.append({"role":"assistant", ...})`；**不**把 user/context 写入跨步历史。每步 `build_messages(trimmed, instruction, ctx.text)` = 历史（system+历次 assistant）+ 本步新 user。因此跨步“重复传输”主要来自：(a) 历次 assistant 中的完整 FILE 回写；(b) 本步 context 对磁盘文件的再次注入；O′ 能省掉的是“最终 messages 中已可见且哈希一致”的本步注入，而不是压缩历史本身。

### 1.3 关键实验结论（已有证据，禁止重新归因）

| 批次 | 资产 | 核心结论（原文口径） |
| --- | --- | --- |
| P1 确认性 | `experiments/p1_validation/p1_experiment_report.md` | F 相对 memory_off / symbol_full_read：prompt/集 **−23.6% / −24.2%**（Holm p=0.0002）；ESR 非劣 PASS（Δ−0.83pp，下界 > −12pp） |
| P2 消融 | `experiments/p2_ablation/p2_ablation_report.md` | **O′ 关闭回升 +397.6 tok/集**（主导机制）；redact −350 但 CMR_visible −7.5pp；闭包 +24 tok、ΔESR=0；**V13B 三轴无差异 → 维持放弃** |
| 双 Token 专项 | `experiments/dualtoken_ablation/dualtoken_report.md` | H-B/H-C **不支持**：B−D/C−D prompt ≈ −29 tok 但 Holm p=0.109，ESR 非劣失败；**C−B ≈ −0.3 tok（两成分不可分离）**；A−D ≈ +403 tok 属 O′/选择性交付，**不得归因双 Token**；B/C 约 20 集/臂为 `EDIT_TARGET_FULL_VERIFY_FAIL` 安全门跳发 |
| 双 Token 补记 v2 | `docs/v12f_validation_preregistration_addendum_dualtoken_v2.md` | P1 集上 B/C 可变换步仅 **39/1360=2.9%** → 剂量不足，预期效应 <1–2 tok/ep；要求独立集剂量 ≥15% |
| V13 holdout（旧 V13A=adaptive） | `experiments/v13_holdout_validation/experiment_report.md` | V13A **最贵**（Δprompt/ep 与 E/F 皆 >0）；ESR 地板 8.3% 三臂相同；失败全为模型能力型 |
| V13B holdout | `experiments/v13b_holdout_validation/v13b_experiment_report.md` | 相对 F：Δprompt −1.5 [−4.5,0]，ESR 持平；相对非 VAM 省 ~140 tok/ep；**ESR 被单任务抖动主导** |
| VSO 故障注入 | `experiments/vso_fault_injection/vso_report.md` | Phase1 联合 PASS（UOR=0/SOR=1.0/FSR=1.0）；Phase2 **30/30**、unsafe=0；**受控注入，非生产故障率** |
| 独立集 | `experiments/independent_validation/` | 预注册已冻结（sha `7023da82…`）；**执行未完成**（审计时 24/720） |

**红线（继承总报告 §9.13）**：

- ✅ 可主张：V12-F 的 prompt 降幅、ESR 非劣、O′ 主导机制、受控注入下 VSO 拦截；
- ❌ 不可主张：双 Token 独立收益；把 A−D 或 V12-F 收益归因双 Token；把 V13B no-body 当作已证明有效；KV 显存下降；VSO 30/30=普遍安全。

### 1.4 旧双 Token 失败根因（设计输入）

1. **模型侧只见 ID/签名行，无确定性展开**：B/C 把相关非目标的 `--- FILE ---` 换成 `--- SYMBOL … ---` / `--- STATIC … ---`（`dualtoken_strategies.transform_plan_related`），指令未命中的符号**没有正文**；模型无法“猜”ID 后面的内容。
2. **剂量不足**：P1 上可变换面 2.9%（补记 v2），省不动 token。
3. **与安全门交互缺陷**：变换破坏了 ET 可见哈希一致性 → `EDIT_TARGET_FULL_VERIFY_FAIL` 跳发 → ESR 非劣失败（报告 §3；属实验包装问题，但暴露“表示变换不得触碰 E/C 路径”）。
4. **C 相对 B 无独立增量**：H-AB 不支持 → “静态签名行”相对“纯符号 ID”在该实现下无分离贡献。
5. **上下文增长率反而更差**：growth（OLS）D=56.1 < B/C=74.2（报告 §2）——旧方案未解决跨步重复，只换了相关非目标的行形态。

### 1.5 对 V12-F 必须调整的点（及回归要求）

| 问题 | 修改必要性 | 对既有结论影响 | 回归方案 |
| --- | --- | --- | --- |
| 本步 context **不进入**跨步历史，O′ 只能证明“assistant 曾写出的 FILE”；相关文件若模型未回写，下一步仍可能重复 FULL 注入 | 降低跨步重复与增长率的主杠杆 | 不改变 O′ 语义（仍要求最终 messages 可见）；可能改变“可省略集合”的大小 → **不改 P1/P2 已冻结数据的解释**，只影响新臂 | 单测：同一文件 step1 注入且哈希不变 → step2 允许以“CR 可见记录”或既有 assistant FILE 证明省略；VSO Phase1 场景 V1/V4/P1/P5 回放必须仍 PASS |
| P0 `StaticStore` 每 episode `open_memory` 删库重建（`run_p1_v12.open_memory`） | 跨任务复用需要**可选**持久层；默认仍可 per-episode | 不影响 V12-F 臂（不启用 CR） | 配置开关 `cr_enabled=false` 时路径与现网逐字节一致（哈希门闩） |
| 相关非目标策略 F=full / E=digest / 旧 V13A=adaptive | CR 只替换“相关非目标的**承载形式**”，不改 E/C/must 规则 | 旧 adaptive 臂结论保持“已跑过、偏负”，不再作为 v1.3A 主臂 | `config_diff` 断言：CR 臂相对 F 仅允许新增字段，不得改 `o_prime/edit_target_oprime_forbid/must_full_dep_closure` 默认值 |

**不修改**：VSO 授权公式、E/C 禁 O′、INSUFFICIENT 门闩、`build_messages`/`SYSTEM_PROMPT` 冻结哈希逻辑（若 CR 需要新 marker，必须走预注册变更，不得静默改 `p1_common`）。

---

## 2. 设计目标与优先级

| 优先级 | 目标 | 主指标 |
| --- | --- | --- |
| P1 | 降低多轮 Context Growth Rate | \(G=\mathrm{OLS\ slope}(\mathrm{prompt\_tokens}, \mathrm{step})\) |
| P2 | 提高记忆复用效率与稳定性 | 复用率、Reference/Memory Integrity、Unsafe Omission=0 |
| P3 | 适当降低 Episode 累计 Prompt Tokens | Episode Total Prompt Tokens（含 Resolver 产物） |
| P4 | 简单、确定、可维护 | 新增结构数、状态数、可单测规则比例 |

硬约束：**不得为 Token 数字牺牲任务正确性**；ESR 非劣与必要信息可见性优先于 P3。

---

## 3. 概念分离（四种对象，禁止混用）

| # | 概念 | 定义 | 例子 |
| --- | --- | --- | --- |
| 1 | **模型 tokenizer 真实 Token** | 由模型词表切分的单位；本设计**不新增** special token | Qwen/DeepSeek 词表中的 `def` |
| 2 | **Prompt 文本标记** | 写入 messages 的普通 UTF-8 文本 | `--- MEM id=… ---` + 展开正文 |
| 3 | **外部内容对象 C** | 记忆库中的逻辑内容单元（含规范化正文） | `content_id=C:a1b2c3d4e5f6` |
| 4 | **外部引用对象 R** | 指向 C 的寻址描述（可独立于正文存在） | `{content_id, pin_hash, range, deps}` |

C/R 是设计角色名；**不代表**两个新的 tokenizer special token。  
模型若收到引用，必须已在同一条最终消息（或 O′ 证明的可见集合）中收到**可读展开**——禁止“裸 ID 待模型自己想象”。

---

## 4. 主方案：CR-Memory

### 4.1 一句话

在 V12-F 的 plan→assemble→pre_send 流水线中插入**内容寻址记忆单元**与**确定性 Resolver**：稳定可复用信息以 C 存储并可按 R 寻址；装配时只把**本步选中且展开后**的内容写入 messages；已可见且哈希一致的内容继续走 O′ 省略；任何解析/版本/依赖失败一律回退 FULL，绝不静默丢信息。

### 4.2 数据流（模型调用之前）

```text
workspace sync（既有）
    │
    ▼
Normalize + Dedup → MemoryStore.put（C 单元；内容寻址）
    │
    ▼
build_plan（既有 E/C/must/r）──► Select：候选 C/R 集合
    │                              （must/ET/C 强制；相关非目标按策略）
    ▼
Resolve + Expand（CR Resolver）
    │  ├─ 已在可见集且 hash 一致 → 标记 omit_candidate（交 O′）
    │  ├─ 需要交付 → 展开 FULL / 紧凑 C / range
    │  └─ 失败 → force_full 磁盘正文
    ▼
assemble（既有 FILE 路径 + 新增 MEM 展开路径）
    │
    ▼
build_messages（冻结函数）
    │
    ▼
Validate（Memory / Reference / Dependency / Final Visibility）
    │
    ├─ 全部通过 → chat_completion
    └─ 任一失败 → 修订 force_full 一轮 → 仍失败则 INSUFFICIENT（不发请求）
```

### 4.3 数据长期存储 vs 每轮再生 vs 进入 messages

| 数据 | 生命周期 | 进入最终 messages？ |
| --- | --- | --- |
| C 单元正文与元数据 | 跨步；可选跨 episode（开关） | **仅当本步 Select+Expand 选中** |
| R 引用表 | 随 Store | 引用本身可写入审计；**不单独作为模型输入** |
| ExpandPlan / Select 结果 | 每步重算 | 否（审计 JSONL） |
| 展开后的 FULL/紧凑正文 | 每步装配产物 | **是**（本步 context） |
| O′ 省略决策 | 每步 | 否（但依赖的可见正文必须已在 messages） |
| Resolver 内部缓存 | 进程内 | 否 |
| system + 历次 assistant | 既有 history | 是（既有口径） |
| `cached_tokens` / DB 字节 | 服务端/磁盘 | **否**（禁止计入“模型输入节省”叙事） |

**统计口径（与现网一致）**：Episode Total Prompt Tokens = \(\sum_s\) API `prompt_tokens_s`，其中每次请求的 `prompt_tokens` 覆盖该次 **全部 messages**（system、历史、instruction、context、以及 CR 展开与任何 Resolver 写入的文本）。检索/展开若只发生在 harness 内存、未写入 messages，则只计入 `Retrieval Overhead` 诊断字段，**不得**从 Episode Total 中扣除。各版本（V12-F / B单ID / C-CR）必须使用同一计量函数。

---

## 5. 形式化定义与算法

以下每个算法给出：输入、输出、核心操作、失败条件、复杂度（适用时）、确定性要求。实现时可合并模块（见 §8），但语义不得含糊。

### 5.1 Memory Unit（内容表示 C）

```text
MemoryUnit := {
  content_id   : str        # 见 §5.2
  body_norm    : str        # 规范化正文（唯一权威正文）
  kind         : enum       # source_full | source_symbol | signature | decision | digest
  origin       : {repo_id?, file_path?, symbol?, step?, task?}
  pin_sha256   : str        # blake3/ sha256(body_norm)，与 content_id 推导一致
  deps         : list[content_id]
  created_at   : ts
  meta         : map        # 只读扩展，不参与寻址
}
```

- **规范化 Normalize（输入 raw 文本 → body_norm）**：统一 `\r\n`→`\n`、去 BOM、行尾空白 strip、文件末尾单换号、Unicode NFC。  
- **失败**：解码失败 / 空正文且 kind=source_full → 拒绝入库，回退磁盘读取路径。  
- **确定性**：同一 raw 字节串 → 唯一 body_norm → 唯一 content_id（与时间戳无关）。

**复杂度**：Normalize \(O(|body|)\)；存储期望 \(O(1)\) 哈希索引。

### 5.2 ID 生成与唯一性

```text
content_id := "C:" + hex( blake3( body_norm )[0:6] )    # 48-bit 截断可配置为 12 hex
```

规则：

1. **内容寻址**：相同 `body_norm` ⇒ 相同 `content_id`（确定性去重的基石）。  
2. 正文任何规范化后变化 ⇒ 新 `content_id`（**禁止**原地改写旧 C 的 `body_norm`）。  
3. 逻辑演进（同一“槽位”换代）用 **Slot**，不复用旧 content_id：

```text
Slot := { slot_id, current_content_id, history: [(ver, content_id, ts)] }
slot_id := "S:" + stable_name     # 如 S:api_contract；由任务/仓库配置给定，不由模型发明
```

4. 碰撞：48-bit 截断在单元数 \(N \ll 2^{24}\) 时碰撞概率可忽略；若 `content_id` 已存在但 `pin_sha256` 不同 → **硬失败**（`ID_COLLISION`），禁止覆盖。

**避免旧引用指向新内容**：R 只允许两种钉扎——

- `pin_content`：`content_id` + `pin_sha256`（正文不可变，天然安全）；  
- `pin_slot`：`slot_id` + `version` + 该版本的 `content_id`+`pin_sha256`（禁止“最新版本”模糊引用进入安全路径）。

### 5.3 Reference Representation（R）

```text
Reference := {
  ref_kind     : content | slot
  content_id   : str          # ref_kind=content
  slot_id      : str          # ref_kind=slot
  version      : int          # slot 钉扎；content 可省略
  pin_sha256   : str
  range        : full | lines(a,b) | symbol(name)
  deps         : list[Reference]
  purpose      : must | related | background   # 仅作 Select 提示，不授予省略权
}
```

**Prompt 文本标记（非 special token）**——仅在正文展开后附带：

```text
--- MEM id=C:a1b2c3d4e5f6 kind=source_symbol range=full ---
<展开正文，与磁盘/单元哈希一致>
```

`purpose=background` 且本步 Select 未选中 → **不写入 messages**（解决“不需要的记忆不进 Prompt”）。

### 5.4 内容去重（Deduplicate）

```text
Dedup(raw) →
  n := Normalize(raw)
  id := ContentId(n)
  if store has id:
     assert store[id].pin_sha256 == Hash(n)   # 否则 ID_COLLISION
     return HIT(id)
  store.insert(MemoryUnit(...)); return MISS(id)
```

- 输入：raw 字节；输出：`content_id` + HIT/MISS。  
- 失败：碰撞、磁盘/DB 不可用 → 调用方不得假装 HIT，走“无记忆”路径。  
- 复杂度：\(O(|body|)\)。  
- 确定性：仅依赖 Normalize+哈希，无随机、无模型调用。

### 5.5 Store / Update（版本管理）

```text
Update(slot_id, new_raw) ->
  n := Normalize(new_raw); id := ContentId(n)
  Dedup insert
  Slot.history.append((ver+1, id, ts)); Slot.current = id
  # 旧 content_id 永不删除正文（审计与旧 R 仍可解析）
```

失败：`slot_id` 未知且未允许 auto-create → `UNKNOWN_SLOT`；禁止静默创建安全路径上的槽位。

**Memory Integrity**：任意时刻 `Hash(unit.body_norm) == unit.pin_sha256`；校验失败的单元标记 corrupt，Resolve 视为 miss。

### 5.6 Resolve（引用解析）

```text
Resolve(R, store) ->
  if R.ref_kind == content:
     u := store[R.content_id] or fail NOT_FOUND
     if Hash(u.body_norm) != R.pin_sha256: fail HASH_MISMATCH
     body := u.body_norm
  else:
     s := store.slots[R.slot_id] or fail UNKNOWN_SLOT
     if s.history[R.version] is None: fail VERSION_NOT_FOUND
     (cid, sha) := s.history[R.version]
     u := store[cid]; assert Hash == sha
     body := u.body_norm
  return Slice(body, R.range)   # range 非法 → fail ILLEGAL_RANGE
```

- 失败条件：`NOT_FOUND | HASH_MISMATCH | UNKNOWN_SLOT | VERSION_NOT_FOUND | ILLEGAL_RANGE`。  
- **禁止**：ID 不存在时静默忽略；版本不明时自动用“最新”；哈希不一致时继续使用。  
- 复杂度：期望 \(O(1)+O(|slice|)\)。  
- 确定性：纯函数（store 只读快照）。

### 5.7 Select（任务相关选择）

在既有 `build_plan` 之后、不改 E/C/must 定义：

```text
Select(plan, instruction, store, cfg) -> set[Reference]
  R := ∅
  # 1) 强制层（与 V12-F 相同义务，只是可能换成“磁盘 FULL”或“C 展开 FULL”）
  for f in plan.must_full ∪ plan.edit_targets ∪ plan.candidate_full:
      R += Ref(content from disk-or-store, range=full, purpose=must)
  # 2) 相关非目标：CR 的可省 token 主战场
  for f in plan.files where level==FULL and not is_must and not is_edit_target and not is_candidate:
      if cfg.cr_related_mode == "compact":      # 默认
          R += Ref(signature_or_compact_C(f), purpose=related)
      elif cfg.cr_related_mode == "full":       # 对齐 F，用于对照
          R += Ref(full(f), purpose=related)
      else:  # none → 不产生 R（等价 NONE）
          pass
  # 3) DIGEST 行：可映射为 kind=digest 的 C，或保持既有 INDEX 行（实现二选一，预注册钉死）
  # 4) 指令词边界命中的符号：在 related 文件内升级 range=symbol（仍不得降级 E/C）
  return R
```

失败：Select 不产生异常；**不完整检索不得被标成完整**——若 workspace 枚举失败 → 整步 `INSUFFICIENT`（既有 `MISSING_REQUIRED_FILE` 语义）。

**防过度拆分**：最小单元默认 **文件级 compact** 或 **符号级**（与 P0 parser 符号粒度一致）；禁止按行任意碎片化。符号过多时按 `K_max` 与预算裁剪**仅可选 related**，must/ET/C 豁免（沿用 V12-F）。

### 5.8 Expand（展开为模型可理解信息）

```text
Expand(R_set, messages_so_far, disk, cfg) -> context_text
  parts := []
  for r in R_set sorted by (purpose rank, path, id):
      if cfg.o_prime and r.purpose != must and Visible(messages_so_far, r) and HashMatch:
          continue   # 交 O′；不写入 parts
      body := Resolve(r) or DiskFull(r.path)   # Resolve 失败 → 磁盘 FULL
      if r.purpose in (must,) or r.range == full and r in E∪C:
          parts += FILE_block(path, body)      # 既有格式，保证 pre_send 正则可解析
      else:
          parts += MEM_block(content_id, body) # 紧凑或全文，正文始终可读
  return join(parts)
```

**铁律**：

1. E/C/must 的展开结果必须仍是 `--- FILE path (full current source) ---` **整文件**且 hash=磁盘——与 `messages_visibility._CTX_FILE_RE`、双 Token 补记“ET 禁止变换”一致。  
2. 禁止只输出 `MEM id=…` 而无正文。  
3. 动态信息：每步以**当前磁盘**为权威；Store 只作复用与去重，**不能**用旧 C 覆盖已变更的磁盘文件（磁盘变更 → 新 content_id，旧 R 失效）。

### 5.9 Validate（四层完整性）

在既有 `verify_omissions_in_messages` **之前/并行**增加：

| 层 | 检查 | 失败动作 |
| --- | --- | --- |
| **Memory Integrity** | 所有本步引用的 C：`Hash(body)==pin` | 丢弃该 R → 磁盘 FULL 或 INSUFFICIENT |
| **Reference Integrity** | R 的 id/version/range 均可 Resolve；无悬空 R | 同上；审计 `REF_DANGLING` |
| **Dependency Integrity** | R.deps ∪ plan.must 闭包：每项要么已展开可见，要么 O′ 证明 | 缺失 → 不得 omit → force_full；仍缺 → INSUFFICIENT |
| **Final Message Visibility** | **既有** O′/E/C 校验（`verify_omissions_in_messages`） | 既有修订一轮 + `*_VERIFY_FAIL` |

**禁止**：把“记忆库存在记录”当成“信息已交付”。交付的定义 = 出现在**最终 messages**（或对 must/ET：出现在本轮 context 的 FULL 且 hash=磁盘）。

### 5.10 Fallback

按优先级：

1. Resolve/校验失败 → 该条目 **磁盘 FULL**；  
2. 修订一轮后 pre_send 仍失败 → `INSUFFICIENT`，**不发请求**（`should_call_model`）；  
3. `cr_enabled=false` 或 Store 打不开 → 完整 V12-F 路径（行为与冻结 runner 一致）；  
4. 任何情况下不得：静默跳过 ID、自动升版本、用 store 正文覆盖磁盘、把 INSUFFICIENT 记成功。

### 5.11 与十个过程的对应（合并说明）

| 过程 | 落点 | 是否独立模块 |
| --- | --- | --- |
| Store | `MemoryStore.put` | 可与 Normalize/Dedup 合并为 `memory_store.py` |
| Normalize | 同上 | 合并 |
| Deduplicate | 同上 | 合并 |
| Reference | `make_ref` / plan 附件 | 合并进 Select |
| Resolve | `resolver.py` 纯函数 | **独立（可测）** |
| Select | `levels.build_plan` 后钩子 | 扩展 levels 或 `cr_select.py` |
| Expand | `assemble` 分支 | 扩展 assemble |
| Validate | `cr_validate` + 既有 messages_visibility | 校验独立，调用点在 pre_send |
| Update | 仅 slot 路径；源码变更靠磁盘权威 | 合并 store |
| Fallback | `should_call_model` + Expand 内 | 已有门闩扩展 |

**不引入**：额外模型调用、多 Agent、动态学习路由、新数据库引擎（默认沿用每 episode 的 SQLite/JSON 文件即可；跨 episode 持久化用可选目录，非必须）。

---

## 6. 指标定义与计量口径

### 6.1 主指标

**Context Growth Rate**

\[
G(e)=\hat\beta_1 \quad\text{其中}\quad \mathrm{prompt\_tokens}_s=\hat\beta_0+\hat\beta_1\cdot s+\varepsilon_s,\ s=1..|S_e|
\]

- 与双 Token 专项一致：task×arm 内 OLS 斜率，再按组汇总均值（`dualtoken` 报告 §4）。  
- **包含**：system、历史 assistant、本步 instruction、本步 context（含 CR 展开与 marker 行）、OUTPUT FORMAT 等**全部**进入请求的文本。  
- **不包含**：仅存在于 DB 的 C 正文（未展开部分）——但其“未节省的重复”应体现在 RTR 与 Episode Total 上。

**Episode Total Prompt Tokens**

\[
P(e)=\sum_{s\in S_e}\mathrm{prompt\_tokens}(s)
\]

口径冻结：API 返回值；若 `usage_source=estimate` 则单独标记并禁止与 API 混主表（现网 `p1_common.chat_completion` 已分列）。

**Peak Context**：\(\max_s \mathrm{prompt\_tokens}(s)\)。

**Retrieval Overhead**：本步写入 context 的 `--- MEM … ---` 头行 + Resolver 诊断行的 chars/4（与 `chars_per_token=4` 一致）；纯 harness 内存操作记 `t_assemble_ms`，不记入 prompt。

**Redundant Token Ratio（RTR）**：步 context 中与先前已发送块同 `content_id`/同 sha 的块 tokens / 总 context tokens（沿用补记 §5 定义，chars/4）。

**Memory Reuse Rate**

\[
\mathrm{MRR}=\frac{|\{c:\ c\text{ 被}\ \ge 2\text{ 次 Expand 选中}\}|}{|\{c:\ c\text{ 本 episode 被选中}\}|}
\]

**Duplicate Transmission**

\[
\mathrm{DT}=\sum_{s}\sum_{c\in\mathrm{Expand}_s}\mathbf{1}[c\text{ 已在 } \mathrm{visible}(s)\text{ 且仍被写入}] \cdot \mathrm{tokens}(c)
\]

目标：启用 O′ 后 \(\mathrm{DT}\to 0\)（与 V12-F 的 verified_safe_omissions 同向）。

**安全与质量**：ESR、SPR、INSURANCE/`INSUFFICIENT` 率、DHO、Unsafe Omission（VSO 口径）、Memory/Reference Integrity 违例数（目标 0）。

### 6.2 一致性要求

- 三臂（A/B/C，见 §10）共用同一 `prompt_tokens` 汇总脚本与同一 `[ctx]` 等长头（V13B 轮已修正臂名伪影）。  
- 禁止用“DB 变小”替代“模型输入变小”。  
- `cached_tokens` 永不进入主效率结论。

---

## 7. 稳定性与正确性保护

| # | 规则 | 实现落点 |
| --- | --- | --- |
| 1 | ID 不存在 → 失败/回退，禁止静默忽略 | `Resolve` → `NOT_FOUND` |
| 2 | 版本不一致 → 禁止自动用未知/最新版 | `pin_slot` 强制 version |
| 3 | 内容变更 → 新 content_id；Slot 升版 | `Update`/磁盘权威 |
| 4 | 依赖不完整 → 阻止不安全省略 | Dependency Integrity + O′ |
| 5 | 非法 range → 失败或回退 full | `ILLEGAL_RANGE` |
| 6 | 哈希不一致 → 拒用该 C | `HASH_MISMATCH` |
| 7 | 最终消息缺必要信息 → 不得正常执行 | 既有 pre_send + INSUFFICIENT |
| 8 | Resolver 异常 → 确定性 fallback（磁盘 FULL 或门闩） | §5.10 |
| 9 | 编辑目标完整性不被 CR 破坏 | E/C 仍走 FILE 整文件路径；CR **禁止**变换 E/C |
| 10 | 库内有记录 ≠ 已交付 | Validate 四层；VSO 仍验最终 messages |

**四类完整性**（必须分列审计字段，禁止合并成单一 `ok`）：

- Memory Integrity：`hash(unit)==pin`  
- Reference Integrity：无悬空、range/version 可解析  
- Dependency Integrity：闭包内每项可见或 O′  
- Final Message Visibility：既有 O′/E/C  

VSO **仍然**只对最终消息做可见性验证；CR 不替代 VSO。

---

## 8. 简单性、模块与集成

### 8.1 最小模块划分

```text
p1/scripts/cr/
  __init__.py
  store.py        # Normalize, Dedup, MemoryUnit, Slot, put/get（可 SQLite 或 JSON）
  resolver.py     # Resolve, Slice, 纯函数
  select.py       # 由 ExpandPlan + instruction 生成 Reference 集
  validate.py     # 四层校验（调用既有 messages_visibility）
  # assemble 扩展放在 v12/assemble.py 的受控分支，避免双装配器漂移
```

**核心接口（建议签名）**：

```text
store.put_raw(raw, origin) -> MemoryUnit
store.get(content_id) -> MemoryUnit | None
resolve(ref, store) -> str          # 抛 CrResolveError
select_refs(plan, instruction, store, cfg) -> list[Reference]
expand_refs(refs, visible, disk, cfg) -> (text, audit)
validate_cr(refs, messages, disk) -> CrCheck
```

### 8.2 数据流 / 状态流

- **状态类型仅两类**：`MemoryUnit`（不可变正文）、`Slot`（可变指针）。  
- 不引入多级编码体系、不引入学习式权重、不引入运行时 LLM 维护记忆。  
- 异常：全部映射到 `CrResolveError(code)` → Fallback 表；不向模型暴露内部栈。

### 8.3 与 V12-F 集成位置

| 阶段 | 钩子 | 是否改动冻结语义 |
| --- | --- | --- |
| sync 后 | `put_raw` 为工作区文件/符号建 C（可选，失败可关） | 否 |
| `build_plan` 后 | `select_refs` | 否（不改 E/C/must 集合） |
| `assemble_v12` | related 非目标：FILE→MEM 展开；**E/C/must 仍 FILE** | 仅相关非目标承载形式 |
| `build_messages` 前 | `validate_cr` + 既有 `verify_omissions_in_messages` | 否 |
| `should_call_model` | 增加 CR 失败原因字符串 | 否（仍 fail-closed） |

配置：`AblationConfig` 新增 `cr_enabled`、`cr_related_mode∈{full,compact,none}`、`cr_persist=off|episode`；**默认关闭时 run_meta 哈希与 V12-F 一致**。

### 8.4 是否真的需要“两个 Token 类型”？

| 选项 | 结论 |
| --- | --- |
| 两个 tokenizer special tokens | **否**。无训练、无词表变更、1.5B/云端模型不可控词表。 |
| 两种逻辑角色 C/R | **是**——存储内容 vs 寻址引用的分离是去重、版本、范围读取的前提。 |
| Prompt 上两种互斥标记语言 | **否**。统一 `MEM` 标记 + 正文即可；C/R 差异体现在外部对象与审计字段。 |
| 相对“单 ID 机制”的真实效率来源 | 不是标记数量，而是：① 内容寻址去重；② 已可见 O′；③ 相关非目标紧凑正文（非裸 ID）；④ 范围读取；⑤ 跨任务可选复用。若实现只剩“短 ID 无正文”，则与失败的 B 臂同构，**应视为设计错误**。 |

**裁决规则（写入预注册）**：若本地实验 C（CR）相对 B（单 ID+同样展开策略）在 \(G\)、Episode Total、ESR 上均无可分离差异，则正式论文/报告中**放弃“双 Token”表述**，只保留“内容寻址记忆 + 确定性展开”；B/C 命名仅作内部消融。

---

## 9. 与旧方案的关系（少量备选比较后选定）

| 备选 | 做法 | 为何不选为主方案 |
| --- | --- | --- |
| 复活 B/C：相关非目标→裸 SYMBOL/STATIC 行 | 旧实验已证：剂量低、ESR 安全门失败、C≡B、G 更差 | 已否定 |
| 只做 history redact | P2：省 350 tok 但 CMR_visible −7.5pp | 伤可见性，不作默认 |
| 重写全部 V12-F 为新框架 | 违背“不重写已验证机制” | 否 |
| **CR-Memory（选定）** | 内容寻址 C + 钉扎 R + 确定性 Resolver + E/C 不动 + O′ 保留 | 满足 P1–P4；可单测；与 VSO 正交 |

主方案唯一；其余仅作对照臂（§10 的 B）。

---

## 10. 最小实验设计：本地 1.5B

### 10.1 环境

- 模型：Qwen2.5-Coder-1.5B-Instruct（Ollama 或既有 llama-server 路径，与 V13 holdout 同栈优先）。  
- 配置冻结：temperature=0、seed=0、max_tokens 与 holdout 对齐（建议 1024 或 2048，**开跑前写死**）、history=keep、d=2、K_max=8、budget=4096、context_window=8192。  
- 目的：**筛选**“是否值得进入 DeepSeek 正式实验”，不要求论文级显著性。

### 10.2 三臂定义

| 臂 | 标识 | 机制 |
| --- | --- | --- |
| **A** | `vam_coder_v1.2_F` | V12-F 基线（零 CR） |
| **B** | `vam_coder_v1.3A_SID` | V12-F + **单 ID 符号寻址**：相关非目标 → `MEM id=…` + **同样**的展开策略（无 Slot/范围/跨任务层） |
| **C** | `vam_coder_v1.3A_CR` | V12-F + **CR-Memory**（C+R+Resolver+四层校验） |

说明：B 与 C 的**模型可见展开算法尽量同构**，差异仅在外部是否有内容寻址/Slot/依赖完整性——这样 H-B 才能回答“双角色是否优于单 ID”。若实现上 B 无法在不引入 Resolve 的情况下安全展开，则 B 降级为“紧凑签名+磁盘按需读”，并在报告中披露实现差。

**若无法准确构造 B/C**（例如安全门再次因变换跳发）：最小替代 = 仅跑 A vs C，并**增加 dry-run 形态门**（ET 整文件、无裸 ID、INSUFFICIENT=0），B 臂标 `not_run` 并说明原因——不得用错误实现硬凑三臂。

### 10.3 规模与任务

- **6 任务 × 3 臂 × 6 Episode = 18 Episode**；每 Episode **4–6 步**；固定任务、参数、预算、安全规则。  
- 任务必须覆盖（每类至少 1 题，建议 6 题一对一覆盖）：

| # | 场景 | 剂量设计要点 |
| --- | --- | --- |
| 1 | 同一函数信息跨轮重复使用 | 步1 注入/回写，步2–n 仍需该函数语义 |
| 2 | 多任务复用同一份记忆 | 同仓库两个 episode 共享稳定签名/常量（`cr_persist=episode` 或顺序双 episode） |
| 3 | 相似内容去重 | 两文件仅空白/格式差或重复常量块 |
| 4 | 已有记忆版本更新 | 中途改函数体 → 旧 R 必须失效、新内容可见 |
| 5 | 局部范围读取 | 指令只依赖某符号/行段，不需整文件（related 路径） |
| 6 | 无关记忆过滤 | 仓库含无关模块，Select 不得注入（NONE） |

- 任务物化与判别性：沿用 holdout 方法——初态 eval 必败、参考解必过、与既有集 hash 交集=0。  
- **剂量门（dry-run）**：CR 可展开的 related 非目标步占比 **≥15%**（对齐补记 v2）；达不到则先改任务再跑，禁止在无剂量任务上解读“机制无效”。

### 10.4 指标与判定

**筛选指标（本地）**：

| 指标 | 通过（进 DeepSeek） | 失败（停） | 需重新设计 |
| --- | --- | --- | --- |
| ESR（C vs A） | 非劣趋势：ΔESR ≥ −0.10 点估计，且无新增 INSUFFICIENT/DHO | ΔESR < −0.10 或 Unsafe>0 或 ET 跳发>0 | 安全门被 CR 打穿 |
| \(G\)（C vs A） | C 的 mean \(G\) ≤ A | C 显著更差（如 >1.2×A） | 展开反而膨胀历史 |
| Episode Total（C vs A） | C ≤ A（允许持平 ±5%） | C > 1.10×A 且无安全/复用收益 | 纯开销层 |
| Memory/Reference Integrity | 违例 = 0 | 任一违例 | Resolver 不确定 |
| MRR / DT | MRR>0 且 DT≈0（O′ 生效） | 长期 DT>0 | 可见性记录错误 |
| B vs C | 记录方向即可 | — | 若不可分 → §8.4 放弃双 Token 命名 |

**通过条件（全部满足）**：安全类 0 违例 + ESR 不塌 + \(G\) 与 Total 不劣于 A + 剂量门通过 + 形态门（无裸 ID、E/C 整文件）通过。  
**不稳定**（rep 间 ESR 翻转主导、或安全门间歇跳发）→ **不得**进入昂贵模型；先修实现或任务。

本地统计：报告点估计与任务级配对差；不强制 Holm/非劣 CI（样本仅 18 集），但必须披露全部失败机制。

---

## 11. DeepSeek 与 Qwen 正式实验规划

**前提**：本地筛选通过，并完成预注册补记（新 sha，冻结先于任何正式请求）。

### 11.1 P1：DeepSeek 正式验证

| 项 | 冻结内容（示例值，开跑前最终钉死） |
| --- | --- |
| 模型 | deepseek-v4.1-flash-1017（与 P1/双 Token 同源） |
| 任务集 | 新独立集或独立集子集 + **寻址友好结构**（剂量 ≥15%，禁与 P1 泄漏） |
| 臂 | A=`vam_coder_v1.2_F`；B=`vam_coder_v1.3A_SID`；C=`vam_coder_v1.3A_CR` |
| 配置 | temperature=0, seed=0, max_tokens=2048, history=keep, d=2, K_max=8 |
| 规模 | 建议 48 任务 × 3 臂 × R=5（或按预算降为 R=3，须预注册） |
| 主比较 | C−A（主）、C−B（双角色增量）；Holm 校正 |
| 主指标 | Episode Total Prompt Tokens、\(G\)、Peak Context；ESR 非劣 margin **−12pp**（沿用） |
| 次指标 | RTR、MRR、Retrieval Overhead、CMR、TPAE/TPSE |
| 统计 | bootstrap seed=20261102, B=10000, cluster=task_id；sign-flip |
| 排除 | 无事后排除；infra 重跑一次；protocol 计 ESR 失败 |
| S5 | 按 dry-run 2× 写入 run_meta |
| 就绪门 | 前 N 集 INSUFFICIENT/DHO/pre_send 违规>0 或三臂 ESR 全 0/全 1 → 只停不调 |

**正式问题**：

1. CR 是否优于单 ID（C−B）？  
2. CR 是否优于 V12-F（C−A）？  
3. 是否降低 \(G\)？  
4. 是否降低 Episode Total（含全部 Resolver 文本）？  
5. ESR/可见性是否非劣且 Integrity=0？

### 11.2 P2：Qwen 跨模型

- 模型：与 P3-A 同族（如 qwen3.8-flash）或用户指定 Qwen 端点。  
- **不合并**绝对 token；只报方向一致性与非劣判定（沿用 P3-A 口径）。  
- 臂、任务集、指标、统计 seed 与 P1 预注册一致；随机化 seed 顺延新值并记录。

### 11.3 冻结清单（开跑前机器核验）

算法版本 sha、任务集 sha、三臂 config digest、SYSTEM_PROMPT/build_messages/p1_common sha、统计 seed、非劣界、排除规则、剂量审计 JSON、`cr_enabled` 默认值、代码快照 sha256（对齐 V13B `run_meta.code_snapshot_sha256` 实践）。

---

## 12. 风险、边界与诚实条款

1. **旧双 Token 的 B/C 结论不能迁移为 v1.3A 的预期收益**；v1.3A 是新机制，必须新数据。  
2. **V12-F 的 −23.6%/−24.2% 与 O′ −398 tok 不得记在 CR 头上**；CR 只主张相对 A/B 的增量。  
3. **无 KV 张量实测** → 禁止显存主张；`cached_tokens` 仅披露。  
4. **VSO 30/31** 为受控注入 → 禁止生产故障率外推；CR 上线后建议 **重放 VSO Phase1 场景矩阵** 作回归（不替代原结论）。  
5. 独立确认性实验（`independent_validation`）审计时未完成 → 本提案不声称独立集已支持任何 v1.3A 结论。  
6. 1.5B ESR 地板与生成抖动（V13/V13B 报告）→ 本地筛选以安全与 token/增长为主，ESR 只作“不塌”门。  
7. 若 CR 的相关紧凑正文在强任务上导致实现错误上升 → 回调 `cr_related_mode=full`（退化为 A 的注入面 + 仍有去重/校验），而不是加复杂度硬撑。

---

## 13. 实施顺序（工程，非多阶段报告）

1. `cr/store.py` + `resolver.py` 单测（Normalize/去重/版本/range/碰撞）。  
2. 接入 `assemble` 相关非目标分支 + E/C 金样回归（`test_v12_r22_edit_safety`、`test_v12_oprime_messages` 必须全绿）。  
3. dry-run 形态门 + 剂量审计。  
4. 本地 1.5B 三臂筛选（§10）。  
5. 通过 → 预注册补记 → DeepSeek P1 → Qwen P2。  

任何一步安全门失败：停、披露、修实现；不进入下一步。

---

## 14. 审计索引（证据路径速查）

| 主题 | 路径 |
| --- | --- |
| V12-F 装配/O′ | `vam-coder/p1/scripts/v12/assemble.py`, `proof.py`, `messages_visibility.py` |
| 计划/闭包/E-C | `vam-coder/p1/scripts/v12/levels.py`, `targets.py` |
| Runner/门闩/history | `vam-coder/p1/scripts/run_p1_v12.py`（`should_call_model`, `history.append`） |
| 消息与计量 | `vam-coder/p1/scripts/p1_common.py`（`build_messages`, `chat_completion`） |
| 旧双 Token 实现/报告 | `vam-coder/p1/experiments/dualtoken_ablation/dualtoken_strategies.py`, `dualtoken_report.md` |
| 双 Token 补记 | `vam-coder/p1/docs/v12f_validation_preregistration_addendum_dualtoken.md` 及 `_v2.md` |
| P1/P2 结论 | `vam-coder/p1/experiments/p1_validation/p1_experiment_report.md`, `p2_ablation/p2_ablation_report.md` |
| 旧 V13A(adaptive)/V13B | `vam-coder/p1/experiments/v13_holdout_validation/experiment_report.md`, `v13b_holdout_validation/v13b_experiment_report.md` |
| VSO | `vam-coder/p1/experiments/vso_fault_injection/vso_report.md` |
| 总报告红线 | `vam-coder/V12F_final_validation_and_submission_report.md` §9.13 |
| P0 存储模型 | `vam-coder/src/vam_coder/models.py`（`MemoryEntry`） |
| 臂配置冲突点 | `vam-coder/p1/scripts/v12/config.py` `_ARMS["V13A"]` |

---

## 15. 结论

1. **v1.3A 主方案 = CR-Memory**：内容寻址单元 C + 钉扎引用 R + 确定性 Resolver，嵌入 V12-F 流水线，**不改** VSO/E/C/INSUFFICIENT 语义。  
2. **效率来自复用与选择，不来自裸 ID**；模型侧只见到展开后的可读正文；四层完整性 + 既有 pre_send 共同守住安全。  
3. **不需要** special token 双 Token；需要的是两种外部逻辑角色。若 C−B 无分离收益，正式表述退回单标记机制。  
4. **先本地 1.5B 筛选**（剂量门 + 安全 0 违例 + \(G\)/Total 不劣），再 DeepSeek/Qwen 冻结确认性实验。  
5. 历史双 Token、旧 V13A adaptive、V13B 的结论保持原判：**不迁移、不重解释、不归因**。

（完）
