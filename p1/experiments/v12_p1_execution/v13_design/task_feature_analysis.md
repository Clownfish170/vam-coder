# V1.3 Task Feature Analysis（执行前特征）

状态：**离线探索性设计**（24 任务 × R3）；不改代码、不跑模型。  
数据：`task_feature_matrix_raw.csv`（由 P1 结果 join 冻结任务 focus/文件数）。

---

## 1. E/F 定义再确认（一致）

| 臂 | 相关非目标 | 来源 |
| --- | --- | --- |
| E | **Digest (INDEX)** | prereg §3.0；`config.py`；RUR02/CFD03 runtime |
| F | **Full (FILE)** | 同上 |
| 共享 | ET FULL、Candidate FULL、VP、must、Kmax=8、d=2 | 代码+psc 144/144 |

---

## 2. 任务级收益（ΔSR = F−E）

| 类型 | 任务 | ΔSR | 说明 |
| --- | --- | --- | --- |
| **F 明显更好** | **v1_CFD03** | **+1.0**（3/3 rep） | 唯一任务级全胜 |
| F 略好（抵消） | v1_RFS01 | 0（1 F_only + 1 E_only） | 不稳定 |
| 相同 | 其余 22 个 | 0 | |
| E 更好 | **无** | 0 | |
| Full 只加 token 不涨成功 | STM03(+90), DEL01(+88), RUR02(+75), IRR01(+36) 等 tie | Δtok>0, ΔSR=0 | 成本无收益 |

**全局** F_only=4、E_only=1；ΔESR≈+4.2pp **几乎全部来自 CFD03**。

### CFD03 机制证据（非偶然猜测）

| 步 | E | F |
| --- | --- | --- |
| step1 上下文 | **仅 INDEX util.py** | **FILE util.py 全文** |
| step1 结果 | pass，但写出 **越界抛错** 的 `clamp` | pass，写出 **夹紧** 的 `clamp` |
| step2（双方仅 FILE app.py） | **fail**（`batch([-1,5])` 触发 util 抛错） | **pass** |

路径：`runs/v1_CFD03_{E,F}_R{1..3}/runner_out/...`  
**结论**：相关文件实现语义在 step1 被 Digest 削弱 → 错误 `clamp` 写入 → step2 失败。  
这是 **执行前可关联** 的类型：**相关文件含任务关键实现体，且 step1 可能改写该实现**。

---

## 3. 执行前可观察特征（候选）

| 特征 | 定义/算法 | 执行前可得 | 来源 | 信息泄漏 | 与 F 优势关联 | 样本充分性 |
| --- | --- | --- | --- | --- | --- | --- |
| F1 跨文件依赖 focus | `tasks_v1.0.episodes[].focus` 含 cross/dep | 是 | 冻结元数据 | 低（非结果） | **部分**：CFD03 属 cross_file_dep；但 CFD01/02 同 focus 无 F 赢 | **不足**（focus 粗） |
| F2 指令点名多文件 | \|{files named in τ}\| ≥2 | 是 | 指令文本 | 低 | CFD03 instr_mentions=2；与 F 赢相关但 CFD01 也=2 | 弱 |
| F3 相关文件含函数体 | 相关文件 AST 含 FunctionDef | 是 | workspace 静态 | 低 | 实现体被改写时 Digest 不够（CFD03） | **机制合理**，关联待验 |
| F4 依赖深度 | dep graph depth≥2 | 是 | parser/store | 低 | CLS01 深但双方都成功 | 无关成功差异 |
| F5 相关文件数 | count related | 是 | 索引 | 低 | 多为 1–3，区分度低 | 弱 |
| F6 需理解调用方交互 | 指令含双方符号 | 是 | 指令+索引 | 低 | 部分 CFD | 弱 |
| F7 Digest 仅有接口无实现 | 相关文件非目标且含可编辑 body | 是 | 静态 | 低 | **CFD03 直接** | 探索 |
| F8 多模块协作 | focus 多类文件 | 是 | 索引 | 低 | 弱 | 弱 |

**禁止**：用 eval_success / 最终 diff / F_only 标签作为运行时输入（泄漏）。

---

## 4. 关联结论（探索性）

1. **Full 收益高度集中**：CFD03；非全库规律。  
2. **执行前最有希望的信号**：相关非目标 **含关键实现体** 且 **指令/步骤可能触及其语义**（F3+F2）。  
3. **仅 focus=cross 不够**（CFD01/02 无增益）。  
4. 多数 tie 任务上 Full **只增 token**——自适应必须能 **默认 Digest** 才能控 TPAE。

---

## 5. 样本限制

- R=3，ΔSR=1 即可“全胜”——**不得**当稳定规律。  
- 规则若在本 24 任务上探索 → 必须标 **exploratory**；验证需 **独立集或冻结规则**。
