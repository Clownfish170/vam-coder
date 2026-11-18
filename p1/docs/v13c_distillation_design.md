# V13C 路线2设计：验证锚定的确定性跨集蒸馏（VAD）

状态：**设计稿（未冻结、未实现）**  
日期：2026-11-10  
定位：在 **VSO/O′ + 任务感知交付** 已有主贡献之上，增加**第二机制**；目标 = **有创新 × 有收益**，且不与文献撞车。

---

## 0. 一句话

> Episode 结束后，用 **纯规则/AST（零 LLM 调用）** 从 **已通过 eval 且经 O′/pre_send 验证的交付** 中蒸馏慢层记忆单元；下一 episode 仅在 **指令命中 + 磁盘 hash 一致** 时，经既有 **ICG/O′ 安全路径** 注入——**蒸馏有出处证明，注入走可见性证明**。

英文工作名（论文用）：**V**erified **A**nchor **D**istillation（VAD）  
或：Proof-Anchored Deterministic Experience Distillation。

---

## 1. 文献碰撞检查（不撞车边界）

| 已核验相关工作 | 它做什么 | **我们不做什么 / 差异** |
| --- | --- | --- |
| **Voyager** (2305.16291) | LLM 试错生成**可执行技能库** | **零 LLM**；不学新 skill 程序，只蒸馏**本仓库已有符号/常量/已验证结论** |
| **Reflexion** (2303.11366) | 语言反馈写入 episodic buffer | **无 verbal reflection**；无自然语言“经验小作文” |
| **MemGPT** (2310.08560) | OS 式分页、对话记忆换入换出 | 不做虚拟上下文 OS；对象是 **代码 workspace 交付**，且受 **O′ 证明**约束 |
| **Generative Agents** 记忆流+反思 | LLM 反思入库 | **无 LLM 反思** |
| **LongMemEval / V2** (2410.10813, 2605.12493) | **评测**长期/经验记忆 | 我们是**机制+确认性实验**，不是新 benchmark |
| **Storage→Reflection→Experience 综述** (2605.06716) | 三阶段演进分类 | 我们停在 **Verified Storage**，主动不做 Reflection 阶段（可作 related work 对照） |
| **TrawMem** (2610.36918) | 任务向 workspace，报告省 token | 相邻；差异 = **可见性证明 + 确定性蒸馏 + 非劣协议** |
| 本项目 **O′/VSO + 选择性交付** | 已有主贡献 | VAD **复用**该证明作蒸馏锚点，**不改** VSO 语义 |

**明确不主张：** 通用 agent 长期记忆、LLM 反思、技能合成、对话记忆 benchmark。

**主张的组合差（推论，报告中标注）：**

```text
已验证交付（O′/pre_send + eval=1）
        ↓ 确定性蒸馏（AST/规则，无 LLM）
慢层单元（content_id + 出处哈希）
        ↓ 下一集：指令命中 ∧ 磁盘 hash 一致
ICG/O′ 安全注入（与 V12-F 同路径）
```

单点都不新；**「蒸馏输入必须是已验证交付」+「注入必须仍过可见性证明」** 这条闭环是差异点。

---

## 2. 与现有论文叙事的挂接

| 论文已有章节 | VAD 如何挂上 |
| --- | --- |
| O′/VSO（机制+故障注入） | **不变**；VAD 的“什么能入库”依赖 O′/pre_send 成功记录 |
| 选择性交付 / must·ET | **不变**；慢层单元只是 related/must 的**额外候选来源** |
| P1 vs memory_off −24% | **不变**；VAD 是在此之上的跨集加成，单独消融 |
| 双 Token（不主张） | **继续不主张** |
| 方法节 | 新增一小节：Deterministic Cross-Episode Distillation |
| 消融 | +1 臂：`F+VAD` vs `F`（主）、`F+VAD` vs `memory_off`（锚） |

**论文故事变成两条腿：**  
1）**步内**：可见性证明下的选择性交付（已有）  
2）**跨集**：验证锚定的确定性蒸馏（新）  

---

## 3. 机制设计（最小实现）

### 3.1 什么能蒸馏（入库门，全部确定性）

仅当**同一 episode 内**同时满足：

1. **交付门**：该内容曾出现在最终 messages（FILE 全文，或 pre_send 通过的注入）  
2. **成功门**：episode `ESR=1`（或步级 `eval_success=1` 的产物文件）  
3. **稳定门**：步末磁盘 `content_hash` 与步内注入 hash 一致（无脏写）  

蒸馏对象（只三类，避免膨胀）：

| 类型 | 抽取方式 | 例 |
| --- | --- | --- |
| **符号签名** | AST：`def/class` 首行 + 返回/签名结构 | `def apply(v) -> …` |
| **常量契约** | 模块级赋值 + 数值 | `RATE = 0.25` |
| **已验证编辑对** | (instruction 模式哈希 → 变更文件集) | 仅审计用，**不直接进 Prompt** |

### 3.2 慢层单元结构（逻辑对象，非 special token）

```text
SlowUnit := {
  content_id,      # 内容寻址（与 C 库同一套）
  kind: signature | const_contract,
  body_norm,       # 紧凑正文（合法 Python 桩或常量表）
  origin: {task_id, step_id, file, sha256},  # 出处 = 已验证交付
  pin_sha256,
}
```

- **零 LLM**、可单测、可回放  
- 存储：`p1/slow_mem/`（JSON/SQLite），**按 repo 内容哈希命名空间**（跨任务共享的前提）

### 3.3 注入规则（与 V13B/ICG 集成，不改 VSO）

下一 episode 每步，在 **ICG 选 related** 之前：

```text
for file f in workspace:
  if 指令词界命中 f 或 其符号 ∧ 磁盘 sha 与 unit.origin 不一致:
      skip（磁盘权威）
  elif 命中 ∧ sha 一致 ∧ f 非 must/ET:
      将 SlowUnit 正文作为 related 候选交给 ICG
      （ICG 选中 → FILE/合法紧凑正文；未选 → 跳过）
  elif f ∈ ET ∪ must:
      走原有 FILE 全量（慢层不替代）
```

**铁律：**

1. 慢层**不得**替代 ET/must 的磁盘 FILE  
2. 注入后仍走 **pre_send / O′**（可见性证明语义不动）  
3. sha 不一致 → **忽略慢层**，磁盘为准  
4. 无 eval 成功的 episode **不写入**慢层  

### 3.4 数据流（总）

```text
[Episode k 成功] 
  → 验证锚（messages FILE ∩ eval=1 ∩ 磁盘稳定）
  → AST 蒸馏 → SlowUnit 入库

[Episode k+1 步 t]
  → build_plan（原 E/C/must）
  → ICG 选 optional related
  → 候选集 = 磁盘 related ∪（命中且 sha 一致的 SlowUnit 展开）
  → assemble（FILE / 合法紧凑）→ pre_send → 模型
```

---

## 4. 创新点表述（论文用，避免 overclaim）

**可以写：**

1. **Verified Anchor**：慢层只从「已交付且 eval 成功」的产物蒸馏——与 Reflexion/Voyager 的“模型自省/试错入库”相对。  
2. **Zero-LLM Distillation**：AST/规则，无额外推理成本、可复现。  
3. **Proof-preserving injection**：跨集复用仍受 O′/pre_send 约束——与 MemGPT 自由换页不同。  
4. **组合协议**：跨集加成用同一套非劣/配对统计，与 P1 对齐。

**不能写：**

- 通用长期记忆 / 生命跨度 agent  
- 技能合成、代码生成式 memory  
- 比 MemGPT/Reflexion「记忆更强」的无对照断言  
- 未做同 repo 多任务时的“跨任务大幅省 token”

---

## 5. 最小实验（创新 × 收益 可检）

### 5.1 任务形态（关键：必须同域多任务）

独立 48 题 **跨题共享少**，慢层难发力 → 用 **同仓库连续 episode 链**：

| 设计 | 值 |
| --- | --- |
| 仓库 | 2–3 个小仓库（与 dose 同风格，过泄漏审计） |
| 链 | 每仓 **6 个顺序任务**（共享常量/签名/约定） |
| 臂 | **A** `v12_F` · **B** `F+VAD`（主） · **锚** `memory_off` |
| 重复 | 链级 R=3（整链顺序跑，非任务乱序） |
| 模型 | 先 1.5B 筛选 → 过门再 DeepSeek |

### 5.2 指标（与现口径一致）

- Episode Total Prompt、Peak、Growth（描述）  
- ESR 非劣 −12pp  
- **慢层专用**：`slow_hit_rate`（步级命中且 sha 一致的比例）、`slow_injected_tokens`  
- 主比较：**B−A**（跨集加成）；锚：B−memory_off、A−memory_off  

### 5.3 过门（1.5B）

1. 安全：INSUFFICIENT=0、DHO=0、ET 仍 FILE  
2. ESR：B ≥ A − 0.10  
3. 效率：链总 prompt B ≤ A（或至少 Peak 不升）  
4. 机制：`slow_hit_rate > 0` 且命中步无 sha 违规  

---

## 6. 实现落点（不动 VSO）

| 模块 | 职责 |
| --- | --- |
| `p1/scripts/cr/slowmem.py` | 蒸馏、入库、命中查询（新） |
| `cr/icg.py` | 候选输入增加 slow units（小改） |
| `run_p1_v12.py` | episode 成功后调 `distill_episode()`；步初 `query_slow()`（小改） |
| VSO / messages_visibility / assemble 语义 | **零修改** |

预估：核心 **~300 行 + 测试**；实验 1 轮链式 1.5B。

---

## 7. 与当前进行中批次的关系

| 批次 | 状态 | 与 VAD |
| --- | --- | --- |
| DS 504 集（F/CR/ICG） | 已完成 | 不改；作 **无慢层基线** |
| DS memory_off 补跑 | **进行中** | 对齐锚 |
| VAD | 本设计 | **新批次**（链式任务 + 新臂） |

---

## 8. 风险与止损

| 风险 | 止损 |
| --- | --- |
| 同仓任务仍无共享 → hit≈0 | 1.5B 链上 dry 统计 hit；&lt;5% 则停，不上海 DS |
| 蒸馏污染（失败 episode） | 成功门+交付门硬约束；单测注入假 origin 必拒 |
| 与 ICG 交互复杂 | slow 仅作候选，ICG/磁盘优先级写死 |
| 审稿认为 = 经验回放 | 正文强调 Verified Anchor + 零 LLM + O′ 注入 |

---

## 9. 下一步（待你确认后执行）

1. 冻结本设计为 v1（或改完再冻）  
2. 建 `slowmem.py` + 单测（假 origin 拒绝、sha 不一致忽略）  
3. 生成 **2 仓 × 6 链** 任务 + 泄漏审计  
4. 1.5B：`F` vs `F+VAD` vs `memory_off` 链式筛选  
5. 过门 → 预注册 DeepSeek  

---

**决策句：** VAD = 在不碰 VSO 的前提下，把「已验证交付」变成「跨集可复用的确定性慢层」，与 Voyager/Reflexion/MemGPT 以 **零 LLM + 证明锚点 + 注入仍过 O′** 切开；收益用 **同仓链式** 实验检验，不用独立 48 题硬撑。
