# development/ — 架构研发与版本演进

只建立**真实存在**的版本；不虚构未来版本。历史以 Git 提交与 `p1/docs`/`p1/results` 证据为准。

| 路径 | 版本 | canonical 文档位置（未移动原因） |
| --- | --- | --- |
| [V1.0/](V1.0/README.md) | 初始架构 | `p1/docs/v1.0/`（`materialize_v1_tasks.py` 引用 taskset 路径） |
| [V1.1/](V1.1/README.md) | 可验证架构（VP/O′） | `p1/docs/v1.1/`（`run_p1_v11.py` 引用 protocol 路径） |
| [V1.2/](V1.2/README.md) | 成熟阶段 → **V1.2F** | `p1/docs/v1.2/` + 根目录冻结预注册 |
| [V1.3/](V1.3/README.md) | 最终阶段 → **V1.3E** | `p1/docs/v13e_*.md`（`prereg_freeze.json`/`run_meta` 硬编码） |

子目录：

- `V1.3/V1.3E/` — 旗舰架构规范与机制说明（本目录内的**新**文档）
- `V1.3/exploration/` — 双 Token / V13A 等探索（**非**核心创新）
- `V1.3/archive/` — V1.3 阶段归档
