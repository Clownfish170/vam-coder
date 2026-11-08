# Git 与冻结资产（P1 门禁）

| 项 | 实测 | 结果 |
| --- | --- | --- |
| Branch | `p1/v1.1` | PASS |
| HEAD | `155f934bc6c565bd304b2b7438259d592bc348c8` | PASS |
| stash@{0} | 存在，未 pop/apply/drop | PASS |
| git 写 | 本轮无 add/commit/push/tag/checkout/reset | PASS |

## SHA256

| 文件 | 结果 |
| --- | --- |
| tasks_v1.0.json | PASS `1f3db009…` |
| formal_runs.csv | PASS `279d80f8…` |
| p1_v1.0_manifest_20261030 | PASS `e82072f4…` |
| 七份 v1.2-r2.2 文档 | 全部 PASS（与验收一致） |

## 实现文件

- `p1/scripts/v12/**`、`run_p1_v12.py`：存在，**本轮未修改**  
- 测试：`p1/tests tests` → **181 passed**（门禁时）  

**Git Integrity：PASS**  
**Frozen Asset Integrity：PASS**
