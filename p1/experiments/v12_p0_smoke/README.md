# v12_p0_smoke — 阶段 B

## 当前状态

| 项 | 状态 |
| --- | --- |
| 阶段 A Preflight | **通过** |
| **阶段 B 最终执行计划** | **已生成** |
| 真实模型请求 / P0 执行 | **尚未授权、尚未执行** |
| P1 | **未执行、不授权** |

## 本目录文件

| 文件 | 说明 |
| --- | --- |
| `preflight_report.md` | 阶段 A 环境核验 |
| `task_mapping.csv` | 8 任务机制映射 |
| `p0_execution_plan.md` | 执行计划（计数/停止/隔离/随机化） |
| `episode_manifest.json` | **32** Episode + 快照哈希 |
| `randomization_manifest.json` | seed=**20261102**，顺序与唯一性检查 |
| `README.md` | 本文件 |
| `_gen_phase_b.py` | 清单生成脚本（可复现） |

## 请求上限

理论 **64**（32×2）；以实际调用为准；禁止凑单。

## 下一步

等待人工审核本计划后，**单独批准阶段 C** 才执行真实模型 Smoke。
