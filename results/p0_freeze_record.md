# P0 冻结记录 —— VAM-Coder

- 冻结日期：2026-10-16
- **P0 freeze commit：`a31a0c1`**（`chore: P0 freeze — P0.3 可信依赖目标/
  import绑定冲突修复与实验记录保护`，47 files changed, +5498/−327）
- 修复前基线 commit：`37bf61c`（`chore: P0 修复前基线快照（pytest 23 passed,
  scenario 6/6）`）
- 验收链：`results/p0_fix_report.md`（轮 1）→ `results/p0_final_acceptance.md`
  （最终轮 + 冻结清单）→ `results/p03_acceptance.md`（P0.3 完成标准判定）

## 冻结前四项核验（全部通过）

1. **86 项与 6/6 场景日志来自当前 P0.3 代码**：
   - `results/p03_pytest.txt` 含 86 个 PASSED，其中 7 项仅存在于
     `tests/test_p03_dependency_targets.py`（旧代码无此文件）；
   - 日志 mtime（18:42）晚于最后源码修改（18:41）；
   - 冻结前对当前工作区**现场重跑**：`86 passed`（exit 0）、
     `ALL PASSED: True`（exit 0），与归档一致。
2. **归档与 Git 基线逐字节一致**：`results/archive_git_37bf61c/` 中 5 个
   文件对 `git show 37bf61c:results/<file>` 的 `cmp` 全部 IDENTICAL；
   MANIFEST 已核对（来源、提交号、文件清单、autocrlf 说明准确）。
   注：`core.autocrlf=true` 下工作区为 CRLF、blob 为 LF——字节级权威以
   归档与 git 对象库为准，去 `\r` 内容一致，`git diff` 视角无差异。
3. **git diff 无无意修改/删除/弱化**：
   - 对基线 `--diff-filter=D` 为空（未删除任何旧文件/旧测试）；
   - 唯一被修改的既有测试 `tests/test_invalidation.py` 为轮 1 记录在案的
     **断言加强**（verify 拒绝路径 + 完整恢复序列，断言 3→8）；
   - `tests/` 全目录无 `@skip`/`xfail`；
   - 原始结果仅 `p0_scenario_report.json` 曾被历史重跑改写：冻结前已从
     git 基线还原（git 视角与 `37bf61c` 无差异），轮 1/2 版本另存
     `results/p0_scenario_report_round1_2.json`；其余原始结果从未变动。
4. **冻结提交与记录**：即本文件与 commit `a31a0c1`。

## 依赖版本（`results/p03_env.txt` 实测）

Python 3.12.10 · Windows-11-10.0.26300-SP0 · tree-sitter 0.26.0 ·
tree-sitter-python 0.25.0 · blake3 1.0.11 · pytest 9.1.1 · sqlite 3.49.1

## 测试命令与结果（冻结态）

```bash
python -m pytest tests/ -v --tb=short     # → 86 passed, exit 0
                                          #   存档 results/p03_pytest.txt
python scripts/run_p0_scenario.py         # → 6/6 ALL PASSED: True, exit 0
                                          #   存档 results/p03_scenario.txt
                                          #   报告 results/p03_scenario_report.json
```

退出码汇总：`results/p03_exit_codes.txt`（pytest_exit=0, scenario_exit=0）。

## 后续注意

- `results/p0_scenario_report.json` 已还原为基线内容，场景脚本今后只写
  `p03_scenario_report.json`，请勿再让任何脚本改写基线文件；
- 对 `a31a0c1` 之后的任何代码变更，需重新执行上述两条命令并另存带新
  版本标识的结果，冻结状态才可继续宣称；
- `p0_final_acceptance.md` §4 清单中“76 passed”条目已由 P0.3 的 86 passed
  实测取代（见 `p03_acceptance.md` §3/§5）。
