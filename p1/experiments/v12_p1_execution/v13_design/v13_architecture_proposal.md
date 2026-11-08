# V1.3 架构提案：自适应 Full/Digest（候选）

**推荐方案：策略 A（保守规则）— 默认 Digest，高信息需求升 Full。**

---

## 1. 推荐规则（可实现伪代码）

```text
related_non_target(f, τ):
  if has_editable_impl(f) and (
       mentions(f.path or symbols(f), τ)
       or f in dep_closure(edit_targets)
       or (related(f) and instruction_touches_module(f))
  ):
      return FULL
  return DIGEST   # 默认，对齐 E
```

- `has_editable_impl`：AST 含 FunctionDef/ClassDef（执行前）。  
- `mentions`：词边界路径/符号（与 ET 解析同源，但 **不** 自动进 ET）。  
- 不改变：ET、C、must、VP、Kmax、d。

## 2. 与 E/F 关系

| | related policy |
| --- | --- |
| E | 恒 Digest |
| F | 恒 Full |
| **V1.3-A** | **条件 Full，默认 Digest** |

## 3. 预期（假设，待验证）

| 指标 | 相对 E | 相对 F |
| --- | --- | --- |
| ESR | 接近或略升（CFD03 类） | 略降或持平 |
| TPAE | **低于 F**（多数 tie 仍 Digest） | 低于 F |
| 安全 | 同 | 同 |

## 4. 实现落点（仅规划，本阶段不改码）

- `v12/levels.py`：related 策略函数替换 `non_target_related` 常量分支  
- `config.py`：新增 `related_policy: e|f|adaptive_a`  
- **不改** assemble VP 路径、targets、messages_visibility  

## 5. A/B/C 取舍

| 方案 | 结论 |
| --- | --- |
| **A** | **推荐**：默认省 TPAE，规则简单可测 |
| B | 与 A 同构（二值），文档并入 A |
| C | 预算内可选，增加调参面，**非默认** |

## 6. 事实 / 假设 / 推测

| 类 | 内容 |
| --- | --- |
| **A 事实（P1）** | F ESR+4.2pp 几乎全在 CFD03；F TPAE+0.8%；安全相同；多数任务 tie 且 F 更贵 |
| **B 假设** | 指令命中+实现体 → 需要 Full（CFD03 机制） |
| **C 推测** | 自适应可在不伤 ESR 下把 TPAE 压回 E 水平 |

## 7. 是否值得进 V1.3 实现

**值得，但限最小实现**：只加 related_policy=adaptive_a + 配置开关 + 单测；**不动** VP/ET。  
先跑最小验证再谈默认切换。
