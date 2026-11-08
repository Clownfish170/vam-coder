# V1.3-M1 Policy Examples（规则示例）

规则：`FULL` iff **implementation_body ∧ (instruction_hit ∨ dependency_touch)**；否则 **DIGEST**。  
ET/C/must **始终 FULL**（不走本策略）。

| # | 源码 | τ / deps | 决策 | 理由 |
| --- | --- | --- | --- | --- |
| 1 | `CONST=1`（无 def） | 任意 | **DIGEST** | no_implementation_body |
| 2 | 有 `def clamp` | τ 不提 util，deps 无 | **DIGEST** | impl but no hit/touch |
| 3 | 有 `def clamp` | τ 含 `util.py` / `clamp` | **FULL** | instruction_hit |
| 4 | 有 `def clamp` | `app.py` deps→`util.py` | **FULL** | dependency_touch |
| 5 | 有 `def` | 同时 hit+touch | **FULL** | 双条件 |
| 6 | 语法错误源码 | 任意 | **DIGEST** | uncomputable → 保守 |
| 7 | 编辑目标 `app.py` | — | **FULL** | ET（非本策略） |
| 8 | must_full 依赖文件 | — | **FULL** | must（非本策略） |

## 运行时审计字段（plan.adaptive_audit）

```json
{
  "relpath": "util.py",
  "implementation_body": true,
  "instruction_hit": true,
  "dependency_touch": false,
  "level": "FULL",
  "reason": "adaptive_a_full:instruction_hit:path_token",
  "uncomputable_reason": ""
}
```

特征均在 **模型请求前** 由静态输入计算。
