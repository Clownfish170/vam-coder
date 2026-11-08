# P1-v1.0 正式实验收尾 · 第一阶段核验报告（BLOCKED）

时间：2026-10-31  
结论：**BLOCKED——按收尾指令 §4.A「任一冻结哈希不一致立即停止」执行停止。**
未启动任何正式 Block A / Block M 模型请求；未修改任何冻结文件。

## 1. 核验结果明细

| # | 检查项 | 结果 | 证据 |
| --- | --- | --- | --- |
| 1 | git status | REVIEW | 分支 `p1/v0.2`；工作区含 v1.0 新增/修改文件（见 §3） |
| 2 | 分支 / HEAD | **PASS** | `p1/v0.2` / `155f934bc6c565bd304b2b7438259d592bc348c8`（与历史一致） |
| 3 | 冻结清单存在 | **PASS** | `p1/manifests/p1_v1.0_manifest_20261030.json` |
| 4 | 冻结清单文件 SHA256 | **PASS** | `e82072f4c222e9927762b383a1e344bcd799d5f08c38486665d7eed8cca696df`（=指令值） |
| 5 | 预声明机制表 SHA256 | **PASS** | `20491be687c3b3c216d3e4e6649dcb3d9285e61b74e4b46455e4d1fd0a3ed732`（=指令值） |
| 6 | tasks_v1.0.json 与清单一致 | **PASS** | live=manifest=`1f3db0090fd62c8f…`；task_set=`p1-v1.0.0-rc1`；24 episodes |
| 7 | 资格 run 完整 | **PASS** | `v1_qual_rep0_20261030_233659/{run_meta.json,per_step.csv}` 存在 |
| 8 | GGUF 存在且哈希一致 | **PASS** | 实时重算 sha256=`9b05dce8089197c866b9f76e1db45de8617cda98d9d06059958cb8ad32c56dfa` = 资格记录 |
| 9 | llama-server 可用 | **FAIL** | `http://127.0.0.1:8080/health` 无响应（exit 7）——服务未启动（可用 start 脚本恢复，属环境项） |
| 10 | runner CLI | **PASS**（含映射说明） | 实测 `--history-policy {keep,redact}`（指令中的 `full` = 实现名 **`keep`**）；`--warmup/--pause-seconds/--manifest/--rep` 均存在 |
| 11 | 磁盘空间 | **PASS** | D: 剩余 32G |
| 12 | 覆盖旧 run 风险 | **PASS** | runner 拒绝写入非空目录；新 run 将用新时间戳目录；`git diff` 对 `p1/tasks`/`p1/manifests`/`p1/results/runs`/P0 源码 = 0 |

## 2. 阻塞原因（核心）

**清单内脚本哈希与当前脚本不一致（2/8）：**

| 脚本 | 清单期望（前16位） | 当前（前16位） | 变更内容与原因 |
| --- | --- | --- | --- |
| `run_p1.py` | `7af56e8b519f72d4` | `a05d8919e1a04848` | 冻结后追加 `tasks_path` 写入 run_meta（可追溯性；**不改变**任何实验行为：装配/计时/模型调用/判据均未动） |
| `check_run_integrity.py` | `d29a97596f56445a` | `172f30eab2b03b40` | 冻结后修复完整性检查器对 v1 任务集的 tasks 路径选择（**仅审计工具**，不在正式 run 执行路径内） |

变更时间线：两者均发生在 `p1_v1.0_manifest_20261030.json` 生成**之后**、
资格收尾阶段（为使 v1 资格 run 通过完整性检查 8/8）。属真实的冻结后代码
修订，**不是**文件损坏。按 rev3.2 §11 与收尾指令，此类情况必须新版本锚定，
不得静默换绑、不得 `--allow-manifest-mismatch` 绕过。

## 3. 其他必须随决策一并确认的协议差异（REVIEW）

1. **样本规模口径**：收尾 Prompt 写 Block A=72 episodes/144 请求、
   Block M=12/24——该计数**未含五组基线**（24×3=72）。冻结设计 rev3.2 §9
   为 Block A=24×5×3=**360** episode-runs（720 请求）、Block M=4×5×3=**60**
   （120 请求）。本次执行准备按 **rev3.2（含基线）** 理解；若按字面 72/12
   执行则实验无基线对照，RQ1/RQ3 无法回答。需用户书面确认口径。
2. 条件 A 参数名映射：Prompt `full` → CLI `keep`（已核实，无实现缺口）。

## 4. 修复方案（待用户选择；本轮不执行）

| 选项 | 内容 | 优点 | 代价 |
| --- | --- | --- | --- |
| **A（推荐）** | 生成**新**清单 `p1_v1.0_manifest_20261031.json`（钉住当前脚本，含 tasks_path/检查器修复），写冻结补充说明；正式 run 使用新清单；旧清单原样保留 | 符合“冻结变更=新锚点”协议；审计链完整 | 需用户批准新锚点 |
| B | 将两脚本手工还原为冻结时内容后开跑 | 沿用旧清单 | 还原 `check_run_integrity.py` 会使 v1 资格审计复核失效；收益为零 |
| C | `--allow-manifest-mismatch` 强跑 | 无 | **违反收尾指令**，不可采用 |

服务项：启动 llama-server（`start_server.bat` 同参数）即可；与哈希无关。

## 5. 本轮实际执行的命令（摘要）

- `git branch/rev-parse/status` → exit 0
- SHA256 核验（manifest/predecl/tasks/脚本/测试/GGUF 实时重算）→ exit 0
- `run_p1.py --help` → exit 0（CLI 核实）
- `curl 127.0.0.1:8080/health` → exit 7（服务未起）
- `git diff --stat`（P0 与冻结目录）→ 0 行差异

**未执行**：任何 Block A / Block M 正式模型请求；任何文件修改；任何 git 提交。
