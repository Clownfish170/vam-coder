# V1.3-M1 Implementation Report

状态：**M1 最小实现完成**；未跑模型；未改 V1.2 冻结文档与实验数据。

## 1. 修改 / 新增文件

| 文件 | 目的 |
| --- | --- |
| **`p1/scripts/v12/adaptive_features.py`** | **新增**：`has_implementation_body` / `instruction_hit` / `dependency_touch` / `decide_related_level` |
| **`p1/scripts/v12/levels.py`** | `policy=="adaptive_a"` 分支；`source_by_file`/`file_deps` 入参；`plan.adaptive_audit` |
| **`p1/scripts/v12/config.py`** | 新增 arm **`V13A`**（`non_target_related=adaptive_a`）；**E/F/G/H 不变** |
| **`p1/scripts/run_p1_v12.py`** | 传入 `source_by_file`；`V12_ARMS` 增加 `V13A` |
| **`p1/tests/test_v13_m1_adaptive.py`** | **新增** 12 项测试 |

**未改**：`v11/**`、`run_p1.py`、tasks、prereg、P1 原始数据。

## 2. 判定特征实现

| 特征 | 实现 | 执行前？ |
| --- | --- | --- |
| `implementation_body` | `ast.parse` 是否含 FunctionDef/AsyncFunctionDef/ClassDef；SyntaxError/缺失 → **None（不可计算）** | 是（静态源码） |
| `instruction_hit` | 路径 basename / stem / 符号 **词边界** 匹配 τ | 是 |
| `dependency_touch` | 以 EditTargets 为种子，depth≤`closure_depth` 的 provider/caller 闭包 | 是（索引 deps） |
| **升级规则** | `FULL` iff `impl AND (hit OR touch)`；否则 **DIGEST** | 是 |
| **保守** | impl=None → **不升 Full**，`uncomputable_reason` 记录 | 是 |

**未使用**：eval、response、成功标签、事后诊断。

## 3. 安全约束（继承 r2.2）

- ET/C 仍强制 FULL；`edit_target_oprime_forbid` 默认 true  
- must 不降级；`should_call_model` 门闩未改  
- `adaptive_a` **仅** 相关非目标的 Full/Digest  
- E/F/G/H 配置值验证：digest/full/full_if_indexed/none **未变**

## 4. 关键代码路径

```text
decide_related_level()          # adaptive_features.py
build_plan(... source_by_file)  # levels.py adaptive_a 分支
plan.adaptive_audit             # 每文件 pre-exec 审计
run_p1_v12 → build_plan(..., source_by_file=files)
```

## 5. 默认行为

- **默认 E/F/G/H 不变**  
- 新策略仅 arm **`V13A`** 或 `non_target_related="adaptive_a"`  
- ARCH_VERSION 仍为 `v1.2-r2.2`（策略可选，未升 r2.3 文档）

## 6. Git

- HEAD `155f934bc6c565bd304b2b7438259d592bc348c8`  
- stash@{0} 未动  
- 无 commit/push/tag  

## 7. 不确定边界

1. AST 仅认 def/class；装饰器-only/类型别名不算实现体。  
2. `instruction_hit` 词边界；同义词/中文“该文件”不命中 → 保守 Digest。  
3. `dependency_touch` 依赖 store deps 质量；无 dep 时仅靠 instruction。  
4. 不可计算 → Digest（可能漏升 Full）。  
5. 未在真实模型上验证 CFD03 类收益（待授权实验）。

## 8. SHA256（本阶段文件）

见 `v13_m1_manifest.json`。
