# P1-v1.0 实施报告（2026-10-30）

## 0. 仓库与起止状态

| 项 | 值 |
| --- | --- |
| 路径 | `D:\Demo\DynaMem\vam-coder` |
| 分支 / HEAD | `p1/v0.2` / `155f934`（**未**创建 commit/tag/push） |
| 开始时工作区 | 4 个 v1.0 文档未跟踪 + llama_server.log |
| 结束时工作区 | 上述 + 全部 v1.0 新增实现/任务/结果（约 46 项 untracked/modified；用户 v0.2 资产未改） |
| 冻结保护 | v0.2 tasks/manifest/runs/审计报告零改动；P0 `pytest tests` 86 passed |

规范来源：`p1/docs/p1_v1.0_taskset_design.md` **rev3.2**；资格 run 的
`tasks_sha256=1f3db009…`；冻结清单 `p1_v1.0_manifest_20261030.json`。

## 1. 实施清单状态（对照 p1_v1.0_implementation_checklist.md）

| 项 | 状态 | 证据 |
| --- | --- | --- |
| P0-1 决策 U1′/U2 | **部分阻塞** | 实现按分支 1（含 redact/Block M 就绪）完成；**R 值与是否开跑正式实验待用户授权**（默认建议 R=3） |
| P0-2 24 任务目录 | ✅ | `p1/tasks/v1_*`（24 project + 48 eval + 24 reference）；`tasks_v1.0.json` v `p1-v1.0.0-rc1` |
| P0-3 参考补丁自检 | ✅ | `selfcheck_v1.py` → **48/48 PASS**（`results/selfcheck_v1_report.json`） |
| P0-4 eval 数值审计 | ✅ | 自检覆盖 CFD01 截断安全、CLS01 14/16/26、行为断言 only |
| P0-5 assemble_audit | ✅ | `result.json.assemble_audit`；单测三样例；O=false 时 omitted_*=0 |
| P0-6 --warmup | ✅ | 资格 run `warmup_requests.jsonl`（3 次，不入 CSV） |
| P0-7 历史度量 | ✅ | `history_file_blocks` / `history_code_chars` 入 CSV |
| P0-8 --pause-seconds | ✅ | 资格 run 使用 2s |
| P0-9 分类器+Q3a/Q3b | ✅ | `check_mechanisms_v1.py` + `qualify_v1.py`；合取逻辑有单测；表哈希锁定 `20491be6…` |
| P0-10 回归 | ✅ | **119 passed**（P0 86 + P1 33） |
| P0-11 冻结必须层 | ✅ | `manifests/p1_v1.0_manifest_20261030.json`（sha `e82072f4…`）+ `results/freeze_v1_0.md`；**tag 未打（待授权）** |
| P1-1 redact | ✅ 实现+单测+dry-run | `--history-policy redact`；`v1_dry_redact_stm01` |
| P1-2 NOTE_INS_VIOL | ⚠️ 部分 | 关键词启发式未单列脚本；诊断文档人工标注违例 |
| P1-3 cached_tokens 汇总 | ⚠️ 未做 | raw usage 已落盘，聚合脚本待 P2 |
| P1-4 耗时校准 | ✅（资格数据代替） | 资格 run 真实 t_model 中位可用 |

## 2. 参考补丁自检（24×2=48）

`python p1/scripts/selfcheck_v1.py` → **48/48 PASS，exit 0**
（每步：初始仓库失败 + 参考补丁通过；报告 `p1/results/selfcheck_v1_report.json`）。

## 3. 测试与命令（真实退出码）

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `python -m pytest p1/tests tests -q` | 0 | **119 passed** |
| `selfcheck_v1.py` | 0 | 48/48 |
| dry-run v1_RUR02 / redact STM01 | 0 | 见 runs/v1_dry_* |
| `run_p1.py` 资格（24×5，warmup=3，pause=2s） | 0 | run `v1_qual_rep0_20261030_233659`（240 步） |
| `check_mechanisms_v1.py`（修订判定层后重判同数据） | 1 | 14 任务机制全过 / 10 任务必需事件缺失（模型违例） |
| `qualify_v1.py` | 0 | OK=11 REVIEW=10 CAP=2 TRIVIAL=1 EXCLUDE=0 |
| `check_run_integrity.py` 资格 run | 0 | **8/8 PASS** |

## 4. 资格结果（Q1–Q6；证据在 run 目录内）

- 标签表：`qualification_report.md`；REVIEW 三分诊断：
  `qualification_diagnosis.md`（**10 个 REVIEW 全部为模型违例**，无实现缺陷/
  规格不可达；含 workspace/response 证据）。
- 判定层修订（重判同一原始数据，非重跑模型）：①方法符号末段匹配
  （`Client.fetch`）；②SIG/REN「调用方 unverified」降 OPT（P0 语义：被模型
  自改的符号标 stale 而非 unverified）——修订原因与时间线已写入诊断文档。
- CAP：REN01、SIG02（五组 step1 全败，分层保留）。TRIVIAL：IRR01（全过+
  省略触发成功，保留作 token 地板）。

## 5. 哈希

| 对象 | sha256（前 16 位+完整见文件） |
| --- | --- |
| 预声明表 | `20491be687c3b3c2…`（资格判定与冻结一致） |
| 冻结清单 | `e82072f4c222e992…` |
| tasks_v1.0.json（资格时） | `1f3db0090fd62c8f…` |
| 模型 GGUF | 见 qual run_meta `model.gguf_sha256`（computed） |

## 6. 模型与服务

llama-server（本机，qwen2.5-coder-1.5b-instruct-q6_k，ctx=8192，parallel=1）；
`/version` 404 → **version=unknown（如实记录）**；usage 含
`prompt_tokens_details.cached_tokens`（raw 已存 request.json/result.json）。
**REUSE_KV 仅为文本上下文省略代理**，本报告不主张任何真实 KV/显存收益。

## 7. Block A / Block M 与预算（未启动正式实验）

| 块 | 规模 | 预算（含 5s 间隔） | 状态 |
| --- | --- | --- | --- |
| Block A（条件 A，RQ1/RQ3） | 24×5×R；R=3 → 360 runs / 720 请求 | ≈55–60 min | **未执行——待授权** |
| Block A R=5 | 600 runs | ≈90–100 min | 备选 |
| Block M（条件 M，RQ2） | 4×5×3=60 runs / 120 请求 | ≈9–10 min | **未执行——待授权**（redact 已验收） |

## 8. 剩余风险与未决

1. 1.5B 在 10 个任务上机制不触发（模型违例）——正式实验中机制触发率将是
   真实结果的一部分，不得事后剔除；
2. NOTE_INS_VIOL 自动检测仍偏人工；
3. 资格 run 的 run_meta 记录的是 draft 清单（判定层修订后脚本有变更；
   冻结清单已重打；正式 run 必须 `--manifest p1_v1.0_manifest_20261030`）；
4. **待用户决策**：U2（R=3/5）、是否开跑 Block A/M、是否授权 git
   commit/tag（工作区含大量新增文件，提交范围需你确认）；
5. cached_tokens 聚合与分析脚本（P2-1）未做。

## 9. 正式实验准入结论

**工程准入：达到**（自检 48/48、回归 119、审计/检查器单测通过、资格 0
EXCLUDE、冻结必须层完成、redact 验收通过、完整性 8/8）。  
**开跑授权：未获得**——等待用户确认 R 值与 Block A/M 预算后，使用冻结清单
执行正式实验。
