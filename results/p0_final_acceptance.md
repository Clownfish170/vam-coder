# P0 最终验收报告（冻结候选） —— VAM-Coder

- 日期：2026-10-16
- 范围：P0 最终轮——仅两个已知解析器问题；架构（Python + SQLite +
  Tree-sitter）不变，无训练、无真实 KV、无学习式路由器、无大规模重构。
- 前序验收：轮 1（A–G）见 `results/p0_fix_report.md`；逐文件变更见
  `PATCH_NOTES_P0_FINAL.md`。
- 一句话结论：**两个问题均有代码修复 + 回归测试在修复前代码上复现 + 全量
  76 passed（exit 0）+ 场景 6/6（exit 0）→ 满足完成标准，建议按下文清单
  冻结 P0**（清单项须人工逐条勾选后冻结）。

---

## 1. 任务 1：解析不完整时禁止使用部分 AST 更新记忆 —— **通过**

实现要点（`parser.py` + `invalidation.py` + `pipeline.py` 文档）：
1. 逐文件状态：**success / partial / failed / unsupported_language**，
   错误原因保留在 `file_errors`、`parse_warnings`（并随 `sync_completed` 落盘）。
2. 仅 `success` 文件的解析结果可更新符号内容依据（content/source hash、
   version）、依赖边与删除判定（阶段 A0 分层）。
3. partial/failed：不覆盖既有哈希/依赖/版本，不 tombstone；既有 valid 符号
   保守收紧为 unverified（`unconfirmed_symbol`，reason 含 `file_partial`/
   `file_failed`），因 unverified 路由必然 EXPAND、禁止 REUSE_KV（有断言）。
   **非全仓库无差别收紧**：只影响不可信文件中的符号（对照测试中 app.py
   lone 在 core.py 坏时保持原状/收紧，其他文件不动）。
4. partial 文件中的新符号不注册为记忆 → `outcome.incomplete_symbols`
   诊断（明确“await complete parse”）。
5. 依赖边裁剪保护：目标文件解析不完整的旧依赖边无法确认消失 → 保留
   （`_deps_with_unconfirmable_held`）。
6. 解析恢复 success 后按既有规则完整同步（测试覆盖：冻结 → 恢复后
   stale/bump → 回退 revert → valid；新符号恢复注册）。
7. 区分保持：真实删除（success 文件缺符号 / 受支持后缀文件消失）仍 tombstone；
   文件读取失败、语法错误、仓库路径错误（抛错中止）、不支持语言各自独立
   分支（`test_parse_guard.py` 全绿）。
8. verify 侧：`has_error`（含符号被部分提取）一律 `verify_inconclusive`，
   不写 stale/tombstone/恢复。

## 2. 任务 2：隔离函数内部 import 的作用域 —— **通过**

实现要点：
1. `extract_import_bindings()` 分层 `{"module": …, "local": {符号: …}}`；
   函数/类体内 import 归属其被索引符号（嵌套函数计入外层，方法记
   `Class.method`），模块级（含模块级 if/try 内）归模块。
2. 模块级 import 只按模块作用域消解；**局部 import 不泄漏给同文件其他
   函数**（任务书场景：function_a 经局部 import 连 `module_a.helper`，
   function_b 不因该 import 连边 → unresolved + `detail`）。
3. 不可靠即 unresolved：局部 import 目标缺失、他函数局部名抑制全局回退、
   同名冲突等一律 `unresolved_calls`（含 detail 原因），零猜测边。
4. 覆盖测试：局部 import、模块级 import、alias（模块级+局部）、跨文件
   同名、无法消歧（`test_import_scoping.py` + 既有 `test_call_resolution.py`）。
5. Python-only 边界保持；完整 Python 作用域语义（绑定时序/条件导入/
   wildcard）明确不支持（README §6.5）。

## 3. 测试执行记录（真实执行，非静态检查）

| 步骤 | 命令 | 结果 | 退出码 | 存档 |
|---|---|---|---|---|
| 本轮修复前既有测试 | `python -m pytest tests/ -v --tb=short` | 63 passed | 0 | `results/p0_final_pre_fix_pytest.txt` |
| 新测试 × 修复前代码（复现） | `python -m pytest tests/test_partial_parse_authority.py tests/test_import_scoping.py -v --tb=line` | **11 failed, 2 passed** | 1 | `results/p0_final_repro_on_prev.txt` |
| 修复后全量 | `python -m pytest tests/ -v --tb=short` | **76 passed** | **0** | `results/p0_final_pytest.txt` |
| 修复后场景 | `python scripts/run_p0_scenario.py` | **6/6 PASS, ALL PASSED: True** | **0** | `results/p0_final_scenario.txt` |
| 退出码汇总 | — | — | 0 / 0 | `results/p0_final_exit_codes.txt` |

- 新增测试 13 项：`test_partial_parse_authority.py`(6，任务 1) +
  `test_import_scoping.py`(7，任务 2)；复现对照逐项见
  `PATCH_NOTES_P0_FINAL.md` §2。
- 既有 63 项全部保留：唯一调整是 `test_parse_guard` 中状态值断言
  `file_read_error` → `file_failed`（随状态重命名，强度不变）；无删除、
  无 skip、无放宽。
- 2 项未在修复前失败的测试原因已说明（防回归性质）。
- 环境无缺失依赖，**无未验证项**。

## 4. P0 冻结检查清单（冻结前逐条人工勾选）

- [ ] 全量测试 `76 passed / exit 0` 可按 README §1 命令复现（本报告已实测）
- [ ] 场景脚本 `ALL PASSED: True / exit 0` 可复现（本报告已实测）
- [ ] 最终轮 13 项新测试在修复前代码的复现记录已归档（`p0_final_repro_on_prev.txt`）
- [ ] 轮 1 A–G 验收（`p0_fix_report.md`）与本轮两任务验收均无“未通过”项
- [ ] README §5 能力表：KV/摘要/token = simulated，EXPAND 读取/推理 = not_implemented；
      决策日志含 `capabilities` 与 `simulated` 字段（`test_capabilities.py` 锁定）
- [ ] README §6 已知限制逐条被接受或列入 P1 待办（见 §5）
- [ ] `PATCH_NOTES.md` + `PATCH_NOTES_P0_FINAL.md` 覆盖全部改动文件，可审查
- [ ] 原始实验记录未被覆盖（`results/pytest_clean_run.txt`、
      `scenario_clean_run.txt`、两轮报告与输出均为独立文件；git 基线 `37bf61c`）
- [ ] 无未提交的意外改动（`git status`：仅本轮声明的源码/测试/文档/结果）
- [ ] 冻结动作：将当前工作区状态提交为 P0 冻结 commit 并打 tag（待用户执行）

## 5. 进入 P1 前仍未解决的限制（合并两轮，如实列示）

**解析与依赖（本轮核心面）**
1. 完整 Python 作用域语义不做：绑定执行顺序（def vs import 时序）、条件
   导入可达性、重导出链、`import *` 消解 → 一律 unresolved（宁漏勿错）。
2. 嵌套函数局部 import 归属外层为近似；类体内 import 不被方法继承——
   均以测试钉住，属已声明近似而非缺陷掩盖。
3. partial 文件在恢复 success 前记忆冻结（含新符号不注册）；指向它的依赖
   边被保留 → 短暂高估覆盖、可能低估传播；恢复后一次性纠正。
4. 语法错误文件中“真删除 vs 解析残缺”恢复前不可区分（方向保守：不墓碑）。
5. 依赖闭包 closure_depth=2 截断；verify 依赖门控 BFS 上限 512 节点、
   快照仅直接依赖；循环依赖有终止无活性保证（环内全 unverified 需逐环解锁）。

**系统性遗留（轮 1 列出、维持不变）**
6. 事务与 JSONL 非原子（缓冲+中止事件策略，不作原子宣称）。
7. 无真实 KV、无 LLM、无动态层、无性能数据（能力三态表锁定）。
8. 单进程 SQLite，无并发/多仓库性能优化；未接入 git diff 级增量。

**P1 准入**：README §8 的四条准入（76 passed 场景全过、两轮回归齐备且
复现记录在案、能力标注无夸大、本清单限制被确认）全部满足后方可开始
P1 基线实验。
