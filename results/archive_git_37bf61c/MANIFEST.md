# 归档：Git 基线 37bf61c 的 results/ 文件

- 来源：`git show 37bf61c:results/<file>`（导出命令执行于 2026-10-16）
- 基线提交：`37bf61c chore: P0 修复前基线快照（pytest 23 passed, scenario 6/6）`
- 校验：5 个导出文件与 `git show 37bf61c:results/<file>` 输出**逐字节一致**
  （`cmp` 实测 2026-10-16，冻结前复核）。注意本仓库 `core.autocrlf=true`：
  工作区检出文件为 CRLF、git blob 为 LF，字节级权威副本以本归档与 git
  对象库为准（工作区文件去 `\r` 后内容一致，`git diff` 视角无差异）。
- 导出文件（与基线字节一致，可用 `git show` 复核）：
  - `pytest_clean_run.txt` —— 轮 1 修复前原始 pytest 输出（23 passed）
  - `scenario_clean_run.txt` —— 轮 1 修复前原始场景输出
  - `p0_scenario_report.json` —— **原始基线 JSON**（工作区同名文件曾被
    场景脚本重跑改写，差异仅为 timestamp 与 request_id；已从本归档还原，
    现工作区版本与基线内容一致；被改写的轮 1/2 版本保留为
    `results/p0_scenario_report_round1_2.json`；P0.3 起脚本改写
    `results/p03_scenario_report.json`，该文件不再被触碰）
  - `p0_fix_baseline_pytest.txt` —— 轮 1 修复前基线记录（23 passed, exit 0）
  - `p0_fix_baseline_scenario.txt` —— 轮 1 修复前场景记录（6/6, exit 0）
