# 预注册补记 P3-A：跨模型泛化实验的模型选定（v1 §9 前置声明）

状态：**已选定并冻结——本声明写于任何 P3-A 模型请求之前；选定后禁止更换。**  
日期：2026-11-06

## 声明内容（填写 v1 §9 的"启动前指定其一"占位）

| 项 | 冻结值 |
| --- | --- |
| **模型（API id）** | **`qwen3.8-flash`** |
| 端点 | `https://maas.qianwenaiapi.com/compatible-mode/v1`（同主实验） |
| 选择依据 | 用户选定；与主实验模型 `deepseek-v4.1-flash-1017` **不同厂商家族** |
| 披露 | 与能力边界模型（本地 Qwen2.5-Coder-1.5B）同属 Qwen 血缘但代际/规模不同；报告按 v1 §9 分模型独立成表，**不与 deepseek 结果合并计算** |
| Preflight（选定前冒烟） | chat 200；usage 含 prompt/completion/**cached_tokens**；FILE 协议正常；completion 含 reasoning_tokens（推理型） |
| max_tokens | **2048**（沿用 v1 冻结的 P1 主预算；跨模型触顶率将在分析中单列披露） |
| 架构 | `vam_coder_v1.2_F` / `memory_off` / `symbol_full_read`（与 P1 相同三臂） |
| 规模 | 48 tasks × 3 × R=5 = **720 episodes**（≤4080 requests） |
| 随机化 seed | **20261109**（仅 episode 顺序，开跑前写入 run_meta；bootstrap 仍为 20261102） |
| 解码 | temperature=0, seed=0, history=keep |
| 分析 | 同 v1 §4（task-cluster bootstrap + sign-flip + 主比较 Holm；效应量+CI 为主）；**只报告方向一致性，不合并原始成功率** |

## 边界

- 本补记仅**填写** v1 预注册已有占位，不改动任何 v1 冻结条款（无需版本升级）。
- P3-B（集内记忆污染 + MEPR）另行设计与声明，不在本补记范围。
