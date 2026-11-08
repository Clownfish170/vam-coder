# V1.3-M1 Test Report

## 执行

```text
pytest p1/tests/test_v13_m1_adaptive.py + V1.2 相关套件 → 61 passed
pytest p1/tests tests → 193 passed
```

（193 = 原 181 + 本阶段新增约 12；以实际 runner 输出为准。）

## 覆盖对照

| 要求 | 测试 | 结果 |
| --- | --- | --- |
| 无实现体 → Digest | `test_no_body_digest` / `test_v13a_default_digest_when_no_signal` | PASS |
| 有实现体、无 hit/touch → Digest | `test_impl_no_hit_no_dep_digest` | PASS |
| 有实现体 + 指令命中 → Full | `test_impl_and_instruction_full` | PASS |
| 有实现体 + 依赖触达 → Full | `test_impl_and_dependency_full` | PASS |
| 双条件 → Full | `test_impl_both_conditions_full` | PASS |
| 特征不可解析 → 保守 Digest | `test_uncomputable_conservative_digest` | PASS |
| ET/C/must 始终 FULL | `test_et_must_always_full_with_v13a` + r2.2 套件 | PASS |
| VP 失败 → 不请求 | `test_vp_fail_insufficient_no_model` + M3-FIX gate | PASS |
| V1.2 E/F/G/H 回归 | `test_efgh_unchanged_configs` + 全量 193 | PASS |
| V13A 计划集成 | `test_v13a_plan_upgrade_and_audit` | PASS |

## 未直接实现的测试

| 项 | 原因 |
| --- | --- |
| 真实模型 CFD03 收益 | **本阶段禁止**跑模型/实验 |
| V13A 端到端 8 任务 dry-run | 可选后续；非 M1 必须；不绕过安全 |

## 结论

**测试通过**；安全约束未绕过。等待人工审核。
