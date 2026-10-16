# P0.3 补丁验收报告 —— VAM-Coder（依赖目标可信性 / 绑定冲突 / 实验记录保护）

- 日期：2026-10-16
- 范围：P0.3 三任务。架构不变（Python + SQLite + Tree-sitter），无训练、
  无真实 KV Cache、无学习式路由器、无 DuckDB、不大规模重构。
- 前序：轮 1 `results/p0_fix_report.md`、最终轮 `results/p0_final_acceptance.md`
  （本报告不覆盖任何旧报告）。
- 一句话结论：**任务 1/2/3 完成标准全部实测满足 → 可建议冻结 P0**
  （须同时满足最终轮报告 §4 冻结清单的人工勾选）。

---

## 1. 修改文件清单与原因

| 文件 | 修改 | 原因（任务映射） |
|---|---|---|
| `src/vam_coder/parser.py` | `parse_repo`：`resolve_dependencies(unique, trusted_targets, …)`——可信索引只含 **success 文件**符号；partial/failed/unsupported 符号留在 `result.symbols` 作诊断 | 任务 1.1/1.2/1.6 |
| 同上 | `_RepoIndex`：文档明确“可信目标边界”；**模块→文件列表去重**（同文件多符号不再被误判模块歧义，修复前 `a.helper()` 多符号模块解析失败） | 任务 1.3/1.7 配套（实测发现的相邻缺陷） |
| 同上 | `_resolve_call`：裸名末位 unknown 补 `detail`（说明只在 success 可信目标中查找）；conflict 分支（见下） | 任务 1.4 |
| 同上 | 新增 `_merge_binds`：同作用域同名**不同目标** → `kind=conflict`（记 targets），同目标重复幂等；`extract_import_bindings` 对 module/local 两作用域都经其合并 | 任务 2 |
| 同上 | `_resolve_call`：局部/模块级/属性绑定遇 `conflict` → `ambiguous_name` + detail，不按树遍历顺序任选 | 任务 2 |
| `src/vam_coder/invalidation.py` | `_deps_with_unconfirmable_held`：只**保留已注册**目标的“解析不完整”依赖边；**未注册目标（含历史遗留悬空边）→ 下一次同步剪除** | 任务 1.5/1.8（不清空全部依赖，逐条判定） |
| `scripts/run_p0_scenario.py` | 场景报告输出改为 `results/p03_scenario_report.json`（带版本标识），不再改写基线 `results/p0_scenario_report.json` | 任务 3.2 |
| `tests/test_p03_dependency_targets.py`（新增，7 项） | 任务 1 回归 | 任务 1.6/1.7/1.8 |
| `tests/test_import_scoping.py`（追加 3 项） | 任务 2 冲突回归 + 同目标重复非冲突 | 任务 2 |
| `README.md` | 可信目标边界、冲突规则、86 测试、`p03_*` 产物与归档指引、准入条件 | 交付（更新 README） |

未修改：`store.py`、`router.py`、`models.py`、`pipeline.py`、`logging_util.py`、
`config.py`、`hashing.py`、`pytest.ini`、`requirements.txt`、`config/default.json`。

## 2. 问题复现方式（新测试 × 修复前代码）

修复前全量：76 passed，exit 0（`results/p03_pre_fix_pytest.txt`）。
新测试在修复前运行：`python -m pytest tests/test_p03_dependency_targets.py
tests/test_import_scoping.py -v --tb=line` → **7 failed，10 passed，exit 1**
（`results/p03_repro_pre_fix.txt`）：

| 失败测试 | 复现的旧问题 |
|---|---|
| `test_partial_symbol_not_used_as_dependency_target` | app.run 经全局唯一裸名回退建边指向 broken.py 未注册 helper |
| `test_import_binding_resolves_to_success_target_only` | `from broken import helper` 绑定解析到 partial 符号并建边 |
| `test_module_qualified_call_with_multi_symbol_module` | 同文件多符号模块被误判歧义 → 可信目标解析失败（去重缺陷） |
| `test_recovery_sync_builds_dependency_after_healed_parse` | 修复前 run 初始即带坏边，恢复流程断言不成立 |
| `test_legacy_dangling_edge_pruned_and_verify_refuses` | 历史悬空边不被剪除（held 规则曾保留未注册目标） |
| `test_conflicting_module_imports_are_unresolved` | `from a import helper` + `from b import helper` 被遍历顺序任选其一 |
| `test_conflicting_local_imports_are_unresolved` | 同一函数内重复绑定冲突同样被任选 |

**10 项通过**（修复前即正确或构造保护）：可信 helper 建边、已注册目标
partial 期间保边、同目标重复 import 非冲突、以及既有 7 项 import 作用域
测试（防回归）。逐项原因如实列示，不将保护性测试的通过冒充复现。

## 3. 测试与场景：真实命令、输出、退出码、环境

| 步骤 | 命令 | 结果 | 退出码 | 存档 |
|---|---|---|---|---|
| 修复前既有测试 | `python -m pytest tests/ -v --tb=short` | 76 passed | 0 | `results/p03_pre_fix_pytest.txt` |
| 新测试 × 修复前（复现） | `python -m pytest tests/test_p03_dependency_targets.py tests/test_import_scoping.py -v --tb=line` | 7 failed, 10 passed | 1 | `results/p03_repro_pre_fix.txt` |
| 修复后全量 | `python -m pytest tests/ -v --tb=short` | **86 passed** | **0** | `results/p03_pytest.txt` |
| 修复后场景 | `python scripts/run_p0_scenario.py` | **6/6 PASS, ALL PASSED: True** | **0** | `results/p03_scenario.txt`、`results/p03_scenario_report.json` |
| 退出码汇总 | — | — | 0 / 0 | `results/p03_exit_codes.txt` |

环境（`results/p03_env.txt`）：Python 3.12.10；Windows-11-10.0.26300-SP0；
tree-sitter 0.26.0；tree-sitter-python 0.25.0；blake3 1.0.11；pytest 9.1.1；
sqlite 3.49.1。**依赖齐全，无未验证项。**

既有测试保留情况：无删除、无 skip、无弱化；P0.3 未修改任何既有测试
（状态值重命名调整属前一轮，已在彼时报告中声明）。

## 4. 实验记录来源表（任务 3.4）

| 类别 | 文件 | 来源 |
|---|---|---|
| **原始基线（Git 37bf61c）** | `results/archive_git_37bf61c/pytest_clean_run.txt`、`scenario_clean_run.txt`、`p0_scenario_report.json`、`p0_fix_baseline_pytest.txt`、`p0_fix_baseline_scenario.txt`（+ `MANIFEST.md`） | `git show 37bf61c:results/<file>` 导出，**5/5 `cmp` 逐字节一致**（冻结前复核） |
| 基线被改写的工作区现状 | `results/p0_scenario_report.json`（轮 1/2 重跑曾改写，差异仅 timestamp/request_id；轮 1/2 版本保留为 `results/p0_scenario_report_round1_2.json`） | **冻结前已从 git 基线还原**（git diff 视角与 37bf61c 无差异；`core.autocrlf=true` 下工作区为 CRLF，字节级副本见归档）。不声称脱离 git 可恢复——可恢复性来自基线提交本身；本轮起脚本改写 `p03_scenario_report.json`，基线文件不再被触碰 |
| **修复前（本轮）** | `results/p03_pre_fix_pytest.txt`（76 passed, exit 0）、`results/p03_repro_pre_fix.txt`（7 failed, exit 1） | 本轮 P0.3 修改前由上述命令真实执行产生 |
| **修复后（本轮）** | `results/p03_pytest.txt`（86 passed）、`results/p03_scenario.txt`、`results/p03_scenario_report.json`、`results/p03_exit_codes.txt`、`results/p03_env.txt` | 本轮修改后真实执行产生 |
| 历史轮次记录（保持不动） | `results/p0_fix_*.txt/md`、`results/p0_final_*`、`results/pytest_clean_run.txt`、`scenario_clean_run.txt` | 各轮当时执行的存档；**旧报告中的测试记录属历史执行，不冒充本次结果**；本次结果仅以 `p03_*` 文件为准 |

## 5. 完成标准判定

| 标准 | 判定 | 证据 |
|---|---|---|
| 不完整文件符号不能成为正式依赖目标 | **满足** | 任务 1.6 场景测试（解析层 deps==[] + 存储层无边 + 悬空边计数 0）修复前 fail / 修复后 pass |
| 可信依赖解析仍正常 | **满足** | success helper 建边、恢复后建边、多符号模块限定、已注册目标保边，4 项测试通过 |
| 新增与既有测试真实通过 | **满足** | 86 passed exit 0；场景 6/6 exit 0（第 3 节命令实测） |
| 实验记录来源清晰 | **满足** | 第 4 节来源表 + git 归档 + `p03_*` 隔离命名 |

## 6. 剩余限制（进入 P1 前需知）

1. 指向未注册目标的历史悬空边**需跑一次 sync 才剪除**（verify 在此之前即
   已能安全拒绝：门控 `dependency missing from store`，有测试）。
2. `unresolved` 的 unknown 类 detail 统一为“仅在 success 目标中查找”表述；
   调用真正语义（如 builtin、外部库）不做进一步区分。
3. import 冲突仅按“同作用域同名不同目标”判定；绑定执行时序、条件导入
   可达性、wildcard、重导出链仍不支持（既定边界，README §6.5）。
4. 部分解析冻结、closure_depth=2 截断、循环依赖活性、事务-JSONL 非原子、
   无真实 KV/LLM/动态层 —— 见 `p0_final_acceptance.md` §5，维持不变。
5. 归档导出依赖本机 git 历史；若仓库 `.git` 丢失，归档目录是唯一基线副本。

## 7. 冻结 P0 判定

**建议冻结**：P0.3 完成标准四条全部满足（第 5 节），全量与场景测试真实
通过。冻结执行前仍须：
1. 按 `results/p0_final_acceptance.md` §4 冻结清单人工逐条勾选
   （其中测试数量已更新为 86）；
2. 将当前工作区提交为 P0 冻结 commit 并打 tag（工作区改动尚未提交，
   待用户确认后执行）。
