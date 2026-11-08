# V1.3-M1 独立只读审计

范围：`adaptive_features.py` / `levels.py` adaptive 分支 / `config` V13A / 测试 / Git。  
约束：只读；未改代码；未跑模型/实验；无 Git 写操作。

---

## 1. AST 实现体识别语义

**位置**：`p1/scripts/v12/adaptive_features.py` `has_implementation_body`（约 L28–47）

| 输入 | 返回 | 含义 |
| --- | --- | --- |
| `FunctionDef` / `AsyncFunctionDef` / `ClassDef`（任意嵌套） | **True** | 有实现体 |
| 仅常量/赋值/import | **False** | 无实现体 |
| 空字符串 | **False** (`empty_source`) | 无实现体 |
| `source is None` | **None** (`source_missing`) | 不可计算 |
| `SyntaxError` | **None** (`syntax_error:*`) | 不可计算 → 保守 Digest |

**能可靠识别**：含 `def`/`class` 的普通 Python 源码。

**不能可靠识别 / 边界**：

| 情况 | 行为 | 风险 |
| --- | --- | --- |
| 空函数体 `def f(): pass` | **True**（仍算实现位点） | 可能过宽升 Full |
| 仅装饰器/类型别名/全局常量 | **False** | 可能漏（若实际有语义） |
| 非 Python / 二进制当文本 | 多半 SyntaxError → None → Digest | 保守，安全 |
| 动态生成代码 | 不可见 | 漏检，保守 |

**结论**：实现与文档“AST 含 def/class”一致；边界已知，**非阻断**。

---

## 2. instruction_hit / dependency_touch（执行前）

| 函数 | 输入 | 执行前？ |
| --- | --- | --- |
| `instruction_hit` | `relpath`、τ、可选 `symbols` | **是**（指令文本） |
| `dependency_touch` | `relpath`、`edit_targets`、`file_deps`、`depth` | **是**（静态图） |
| `decide_related_level` | 上述 + `source` | **是** |

**未使用** eval、response、成功标签、事后诊断 → **PASS**。

**边界**：

- `instruction_hit`：路径 basename、stem（≥3 字符）、symbols 词边界；中文近义/“该文件”不命中 → 不升 Full（保守）。  
- **WARNING（非阻断）**：`levels.py` 调用 `decide_related_level(..., symbols=None)`——**符号命中路径在 plan 集成中未启用**，仅路径/stem 生效。

---

## 3. 依赖触达 vs 既有闭包 / d=2

| 检查 | 结果 |
| --- | --- |
| depth 默认 | `cfg.closure_depth`（=2）传入 `dependency_touch` |
| 与 must 闭包算法 | 同为 provider BFS + caller BFS，depth 同源 |
| 深度行为实测 | a→b→c：depth=1 不触 c，depth=2 触 c **PASS** |
| 过度升级 | 文件若在 provider 闭包内，**通常已进 must_full**，在 `if rel in must` **先于** adaptive → 不会因 adaptive 二次 FULL 重复计入 must |

**WARNING（非阻断）**：对 **非 must** 的相关文件，`dependency_touch` 往往为 False（真依赖多半已是 must）→ 实际升级主要靠 `instruction_hit`；`dependency_touch` 在 adaptive 路径上 **近乎冗余**，不构成错误 Full 扩张。

---

## 4. adaptive_a 影响范围（levels.py）

**位置**：约 L250–349

执行顺序（关键）：

1. **EditTargets / CandidateFull** → 强制 FULL（L255–271）— **不进** adaptive  
2. **must_full** → FULL（L273–285）— **不进** adaptive  
3. 仅当 `policy=="adaptive_a" and r>=1`（相关非目标）→ `decide_related_level`  

| 约束 | 结果 |
| --- | --- |
| ET/C 不被降级 | **PASS** |
| must 不被降级 | **PASS** |
| 仅相关非目标 | **PASS**（`r>=1` 且非 E/C/must） |
| 无关文件 | 走 `non_target_unrelated=none` → NONE |

---

## 5. adaptive_audit 可追溯性

每文件记录（L320–329）：

- `relpath`  
- `implementation_body` / `instruction_hit` / `dependency_touch`  
- `level` FULL|DIGEST  
- `reason`（含 upgrade 原因或 digest 原因）  
- `uncomputable_reason`  

并入 `ExpandPlan.audit()["adaptive_audit"]`。  
来源：**决策时**静态特征，非事后补造。 **PASS**。

---

## 6. V13A 注册与默认策略

| 臂 | non_target_related | ET 禁 O′ |
| --- | --- | --- |
| E | digest | True |
| F | full | True |
| G | full_if_indexed | True |
| H | none | True |
| **V13A** | **adaptive_a** | True |

- E/F/G/H **未改** → 默认行为不变 **PASS**  
- `load_arm("V13A")` 仅 opt-in  
- `run_p1_v12` 新增 baseline `vam_coder_v1.3_V13A`，不替换 E–H  

---

## 7. 测试覆盖

| 套件 | 结果 |
| --- | --- |
| `test_v13_m1_adaptive.py` | **12 passed** |
| 全量 `p1/tests tests` | **193 passed** |

| 边界 | 覆盖 |
| --- | --- |
| 无实现体 Digest | 有 |
| 有 body 无 hit/touch Digest | 有 |
| body+hit / body+touch / 双条件 Full | 有 |
| 不可计算保守 | 有（syntax error） |
| ET/must FULL | 有 |
| VP 失败不请求 | 有 |
| E/F/G/H 配置不变 | 有 |
| 词边界 instruction_hit | 有 |

**非理想输入**：语法错误、空源、无 def、无信号。  
**缺口（非阻断）**：  
- 未测 `symbols=` 命中（plan 传 None）；  
- 无 V13A 端到端 dry-run（本阶段可不要求）。

---

## 8. Git 状态

| 项 | 值 | 结果 |
| --- | --- | --- |
| Branch | `p1/v1.1` | PASS |
| HEAD | `155f934bc6c565bd304b2b7438259d592bc348c8` | PASS |
| stash@{0} | 未动 | PASS |
| Git 写 | 无 | PASS |
| V1.2 冻结文档 | 未改 | PASS |

---

## 9. 问题分级

### 阻断（BLOCKING）

**无。**

### 非阻断（NON-BLOCKING）

| ID | 问题 |
| --- | --- |
| NB1 | `symbols=None`：plan 路径未用符号级 instruction_hit |
| NB2 | `dependency_touch` 对非 must 文件近乎冗余（真依赖多已 must） |
| NB3 | 空 `def` 仍算 implementation_body（可能过宽） |
| NB4 | 无 V13A dry-run/模型验证（按任务范围未做） |
| NB5 | stem 词边界可能过宽（短词） |

---

## 10. 最终结论

# PASS

**理由**：  
- 特征均为执行前静态；  
- adaptive **仅** 作用于相关非目标；ET/C/must **无降级**；  
- 安全门禁与 E/F/G/H 默认 **未破坏**；  
- **193 passed**；Git/冻结 **正常**；  
- 非阻断问题已记录，**不**需为 M1 验收阻塞，亦**不**在本审计中扩展实现。

**不启动 V1.3 验证实验。** 等待人工审阅本报告。
