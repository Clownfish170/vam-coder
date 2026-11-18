# ARCHITECTURE_OVERVIEW — 架构总览

状态：**ACTIVE**  
项目：**VAM-Coder** · 旗舰：**V13E**

## 演进主轴

```text
V1.0 初始架构
  → V1.1 可验证架构（VP/O′）
    → V1.2F 成熟版本（F 选择性交付 + 编辑安全）
      → V13E 最终旗舰（F + S1 + 辅助 S2）
```

## 三层代码

| 层 | 路径 | 角色 |
| --- | --- | --- |
| 产品库 | `src/vam_coder/` | **唯一**可运行产品入口 |
| 实验 harness | `p1/scripts/{v11,v12,cr}/` | 装配、VP、S1/S2、runner |
| 通用工具 | `scripts/` | 维护/分析脚本 |

## V13E 机制一览

- **VP**（Visibility Proof，旧名 O′）— 核心  
- **F**（Selective Context Delivery）— 核心基座  
- **S1**（Verified History Projection）— 核心增量  
- **S2** 义务账本 — **辅助启发式**  
- **MOFF** — 全仓上下文对照策略（非外部 Agent）

详细：[ARCHITECTURE_V13E.md](ARCHITECTURE_V13E.md) · [MECHANISM_VISIBILITY_PROOF.md](MECHANISM_VISIBILITY_PROOF.md)

## 目录职责

见根 [README.md](../README.md)。实验物理数据在 `p1/experiments/`，组织索引在 `experiments/`。
