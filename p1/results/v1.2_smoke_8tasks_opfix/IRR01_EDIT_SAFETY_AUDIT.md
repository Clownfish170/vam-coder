# IRR01 E/step2 编辑安全只读根因审计

数据：`p1/results/v1.2_smoke_8tasks_opfix/` + 冻结任务 `p1/tasks/v1_IRR01` + `tasks_v1.0.json`  
约束：只读；未改代码/参数；未重跑模型。

---

## A. alpha.py 是否真实编辑目标？

**是。**

冻结任务 step2：

```text
只新增 alpha.py 的 a2() 返回 a()+1。不要修改 beta.py。
```

| 步 | instruction | eval |
| --- | --- | --- |
| step1 | 只修改 alpha.py：a() 返回 10 | step1 |
| step2 | 只新增 **alpha.py** 的 a2()…；**不要修改 beta.py** | step2 |

- **预期写入目标**：`alpha.py`（新增 `a2`，**不得**丢掉已有 `a`）。  
- **beta.py**：仅“不要修改”——**负向约束**，不是要求编辑的写入目标。  
- 写入协议：整文件 `FILE:` 覆盖（无 merge/patch 保留机制）。

---

## B. edit_targets 与 must_full

### E/step2 审计原始值（injection_audit）

| 字段 | 值 |
| --- | --- |
| `edit_targets.exact_paths` | **`['alpha.py', 'beta.py']`** |
| `must_full` | **`['alpha.py', 'beta.py']`** |
| levels | alpha FULL (must)，beta FULL (must) |
| omitted | **`['alpha.py']`** |
| injected | `['beta.py']` |
| pre_send | `ok=true`，`omitted_after=['alpha.py']` |

### 解析原因

`parse_edit_targets` 对 step2 指令：

- `path_exact:alpha.py` → 正确  
- `path_exact:beta.py` → 因指令含字面 `beta.py`（否定句）也进入 exact → **整句无否定过滤**  
- 于是 **beta 被抬成 must_full 并注入**（过度注入）  
- **alpha 是真 must**，仍被 O′ 省略（见 C）

### 为何 alpha 未“强制注入上下文 FILE”？

**不是 must_full 集合漏掉 alpha**（集合正确包含 alpha）。  
而是装配允许：**must_full ⊆ injected ∪ O′_proved_omit**（r2.1 方法设计）。  
alpha 在历史 messages 中有完整 FILE（step1 assistant）且 hash 与 step2 磁盘一致 → **O′ 放行省略** → 当前步 context **无** alpha FILE。

**对照冻结设计**：  
- 「必须注入」= **Full 进入当前 context**，或 **O′ 证明后省略**（ok 谓词）。  
- 本步 **未违反**「must_full 集合定义」；**符合**「must 可被 O′ 安全省略」。  
- **但**与「整文件覆盖编辑协议」组合时，**违反编辑安全直觉**（见 D）。

---

## C. 上下文 / 历史 / 哈希

### E/step2

| 层 | alpha 内容 |
| --- | --- |
| 当前 user context | **无** alpha FILE；仅有 `--- FILE beta.py ---` |
| 历史 assistant（step1） | `FILE: alpha.py` + `def a(): return 10` |
| step1 assistant hash | `9bd58a3d…`（与 step2 发送时 disk 一致） |
| pre_send | 认为 messages 中有完整 alpha → **ok** |

发送时 messages：`system + assistant(alpha 全文) + user(仅 beta)`。  
**当前编辑基线（磁盘）** 在 step2 装配前为 `a() -> 10`；模型若省略 alpha 的当前 context，只能依赖历史中的 `a():10`。

### 与 D/step2 对比

| | E | D (v1.1) |
| --- | --- | --- |
| context FILE | 仅 beta | **alpha + beta 全文** |
| 历史 assistant | 有 alpha | 有 alpha |
| 模型输出 | **仅 a2()，整文件** | **a() + a2() 完整文件** |
| 写入后 workspace | 只有 a2 | a + a2 |
| eval | NameError: a | **pass** |

---

## D. 解析 / apply / 写入语义

| 步骤 | 行为 |
| --- | --- |
| 解析 | `FILE: alpha.py` + 围栏 → 整文件内容 |
| apply | **整文件覆盖写入**，无“保留未提及函数” |
| 模型输出 | 仅 `def a2(): return a()+1` |
| 结果 | **`a()` 被覆盖删除** → 测试 NameError |

**事实**：`apply.json` applied=`['alpha.py']`，rejected 空 → 写入成功，但是 **错误内容**。  
**不存在** 未修改内容保留机制（与 D 的“模型写全文件”路径不同）。

---

## E. 最终回答

| 问题 | 答案 |
| --- | --- |
| alpha 是否真实编辑目标？ | **是**（step2 要求新增 a2，并隐含保留 a） |
| 为何未被 must_full 强制注入 context？ | **must_full 已含 alpha**；因 **O′ 证明历史可见** 而省略当前 context FILE（设计允许 must∪O′） |
| 若不是目标为何还要保留原内容？ | （适用）整文件协议下，任何对 alpha 的 FILE 输出都必须是 **完整当前文件**；即使目标只是新增 a2 |
| 根因分层 | **1) 写入语义=整文件覆盖**（主因链） **2) O′ 对编辑目标 must 的省略**（使模型看不到当前完整 alpha） **3) 模型只输出增量函数** **4) 次要：beta 误入 must（否定句路径匹配）** |
| 是否违反冻结设计？ | **对 must_full 集合与 O′ 可见性：未违反 r2.1**（ok=injected∪O′）。 **对“安全编辑”隐含目标：设计缺口**——O′+整文件覆盖组合可丢函数。 |
| 最小修复方向（只提不实施） | **P1（推荐）**：凡 `edit_targets` 内文件 **禁止 O′ 省略**（始终 context FULL）。**P2**：否定指令不产生 exact（“不要修改 X”）。**P3**：协议改为 diff/合并（大改，不推荐本阶段）。优先 **P1**，兼做 P2 减少 beta 误注入。 |

---

## 结论一句话

**alpha 是正确识别的 must，却因历史可见被 O′ 从当前上下文拿掉；模型在整文件覆盖协议下只写了 a2，丢了 a()。**  
这是 **组装策略（O′×编辑目标）与写入语义的交互缺陷**，不是 must_full 漏检，也 **不是** 对 r2.1 O′ 公式的字面违反。

审计结束；等待人工审核。
