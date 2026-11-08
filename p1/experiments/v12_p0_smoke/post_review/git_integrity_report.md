# Git 与冻结资产核验（P0 后）

只读；未执行 git 写操作。

## Git

| 项 | 实测 | 预期 | 结果 |
| --- | --- | --- | --- |
| Branch | `p1/v1.1` | 同 | **PASS** |
| HEAD | `155f934bc6c565bd304b2b7438259d592bc348c8` | 同 | **PASS** |
| stash@{0} | `On p1/v1.1: !!GitHub_Desktop...` | 存在且未 pop/apply/drop | **PASS** |
| git add/commit/push/tag | 未执行（本审查） | 禁止 | **PASS** |

## V1.0 冻结资产

| 文件 | SHA256 | 结果 |
| --- | --- | --- |
| tasks_v1.0.json | `1f3db0090fd62c8f934ed1271b28d0f955c9763fe2956efb30d2a12179f00339` | **PASS** |
| formal_runs.csv | `279d80f8c2a4f9e608395bf891ba91541517193dc7548e9e57dae8bacf9c2375` | **PASS** |
| p1_v1.0_manifest_20261030.json | `e82072f4c222e9927762b383a1e344bcd799d5f08c38486665d7eed8cca696df` | **PASS** |

## V1.2-r2.2 七文档

| 文档 | 结果 |
| --- | --- |
| architecture / method / prereg / roadmap / novelty / review_response / change_note | **全部 PASS**（与验收哈希一致） |

## M1–M4 / M3-FIX-01

- 本审查 **未修改** `p1/scripts/v12/**`、`run_p1_v12.py`。  
- 工作区中上述文件仍为未跟踪状态（与验收时一致）。  
- **PASS**（无未授权改码证据）。

## 结论

# Git Integrity: PASS
