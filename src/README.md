# src/ — 唯一可运行产品代码入口

| 路径 | 说明 |
| --- | --- |
| `vam_coder/` | 产品包：parser、store、router、pipeline 等 |
| `shared/` | 预留跨模块共享工具（**禁止**从 `p1/scripts` 复制粘贴维护两份逻辑） |

**实验 harness**（runner、装配、VP/S1/S2）位于 `p1/scripts/`，服务于冻结实验路径，**不是**第二产品入口；避免复制代码。

测试：`tests/`（产品）、`p1/tests/`（实验机制）。
