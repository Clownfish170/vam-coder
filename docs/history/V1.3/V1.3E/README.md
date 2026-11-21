# docs/history/V1.3/V1.3E — 旗舰版本

状态：**ACTIVE** · 正式写法 **V13E**（并用 V1.3E）

## 机制（核心）

| 机制 | 全称 | 实现 |
| --- | --- | --- |
| **VP** | Visibility Proof（旧名 O′） | `p1/scripts/v11/visibility.py` |
| **F** | Selective Context Delivery | `p1/scripts/v12/assemble.py` + 臂 F |
| **S1** | Verified History Projection | `p1/scripts/v12/history_project.py` |
| **S2** | 义务账本（**辅助启发式**） | `p1/scripts/v12/obligations.py` |
| **MOFF** | Memory Off 全仓倾倒对照 | 臂 `MEMORYOFF`（非外部 Coding Agent） |

## 本目录

- `architecture/` — 规范文档副本说明（正文见 `docs/ARCHITECTURE_V13E.md`）
- `mechanisms/` — 见 `docs/MECHANISM_VISIBILITY_PROOF.md`
- `configuration/` — 臂定义指针 → `p1/scripts/v12/config.py`
- `documentation/` — 指针
- `release/` — 发布说明（待授权开源后填）
- `implementation/` — **不复制代码**；唯一产品入口 `src/vam_coder/`，实验 harness `p1/scripts/`

## 主实验

`experiments/V13E/`（物理数据 canonical：`p1/experiments/v13e_*`）
