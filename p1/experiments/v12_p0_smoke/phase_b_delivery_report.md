# V1.2-r2.2 P0 阶段 B 交付报告

## 1. 修改 / 新增文件（仅 `p1/experiments/v12_p0_smoke/` + 提示词归档）

| 文件 | 说明 |
| --- | --- |
| `task_mapping.csv` | 8 任务机制映射（EXPECTED/NOT/UNCERTAIN） |
| `p0_execution_plan.md` | 执行计划 |
| `episode_manifest.json` | 32 Episode + 快照哈希 |
| `randomization_manifest.json` | seed=20261102 |
| `README.md` | 阶段状态 |
| `_gen_phase_b.py` | 可复现生成脚本 |
| （阶段 A 已有）`preflight_report.md` | 环境核验 |
| `p1/docs/v1.2_p0_smoke_execution_prompt.md` | 提示词归档（更早） |

**未改**：M1–M4 代码、V1.0 资产、r2.2 设计文档、任务集。

---

## 2. 任务映射核验

| task_id | 步数 | 冻结源 | 结果 |
| --- | --- | --- | --- |
| 全部 8 个 | **2** | `tasks_v1.0.json` + `project/` | **PASS** |

机制列含 EXPECTED_TRIGGER / NOT_EXPECTED / UNCERTAIN；执行后才可标 TRIGGERED。

---

## 3. 32 Episode 核验

- 数量 **32**；`episode_id` **唯一**；无重复/遗漏  
- `expected_steps=2`  
- `status=PLANNED`  
- **PASS**

---

## 4. 工作区隔离证明

- 每 Episode 记录 `initial_workspace_snapshot` = `p1/tasks/<id>/project`  
- `initial_workspace_hash` = 该目录全文件清单 sha256（见 manifest）  
- 规则：独立 copytree；Arm 不继承；step2 仅用本 Episode step1 状态  
- **PASS**（计划层；阶段 C 须按此执行并落盘 diff）

---

## 5. 随机化

| 项 | 值 |
| --- | --- |
| seed | **20261102** |
| method | `random.Random(seed).shuffle` |
| uniqueness | all_unique=True, count=32, missing=[] extra=[] |
| 示例序首 | `v1_RFS01_H_R1` → … → `v1_CFD01_E_R1` |

**PASS**

---

## 6. 预计请求上限

**64**（32×2）；INSUFFICIENT 等可减少实际调用；**禁止**凑满 64。

---

## 7. 失败计数规则

见 `p0_execution_plan.md` §7（INSUFFICIENT 分列、禁止自动重试、NOT_TRIGGERED≠PASS 等）。 **PASS**

---

## 8. Git 状态

| 项 | 值 |
| --- | --- |
| 分支 | `p1/v1.1` |
| HEAD | `155f934bc6c565bd304b2b7438259d592bc348c8` |
| stash | `stash@{0}` 未动 |
| git 写操作 | **无** |

---

## 9. 冻结资产哈希

V1.0 三项 + 七份 r2.2 文档：与验收清单 **一致**。 **PASS**

---

## 10. 尚存风险

1. 阶段 C 隔离与日志依赖 runner 输出对齐计划（需执行时对照）。  
2. 64 为上限，实际可能更少——报告须区分计划/实际。  
3. 无统计功效——仅 Smoke。  
4. `_gen_phase_b.py` 为生成器，非实验代码。

---

## 11. 是否具备进入 P0 执行条件

# PASS

计划完整、32 Episode 可复现、随机化可复现、冻结资产无风险。  

**阶段 B PASS ≠ 阶段 C 授权。**  
等待你单独批准真实模型 P0 Smoke。
