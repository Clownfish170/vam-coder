# 环境检查（P1 最终准备）

时间：2026-11-02T05:07:31Z

| # | 项 | 结果 | 说明 |
| --- | --- | --- | --- |
| 1 | Q6_K 模型文件 | **PASS** | `.../qwen2.5-coder-1.5b-instruct-q6_k.gguf` 1,464,178,752 bytes |
| 2 | `/v1/models` HTTP 200 | **FAIL（当前）** | WinError 10061 connection refused — **服务未运行** |
| 3 | 模型 ID 与预期一致 | **NOT_VERIFIED**（服务未起） | P0 时曾返回 q6_k 路径 ID |
| 4 | ctx=8192 可核验 | **PASS（历史）** | P0 启动参数 `-c 8192`；当前进程不存在 |
| 5 | parallel=1 可核验 | **PASS（历史）** | `--parallel 1` |
| 6 | 磁盘 ≥5GB | **PASS** | D: free ≈ **34.09 GB** |
| 7 | 运行参数符合预注册 | **PASS**（代码默认） | seed/temp/max_tokens 见 compliance |
| 8 | 检查时间记录 | **本文件** | 上方时间戳 |

## 启动服务说明

本轮 **未** 启动 llama-server（避免任何非必要进程操作；且非 P1 任务请求仍需用户授权后的健康检查）。  
**P1 开跑前**：启动服务 → `/v1/models` 200 → 核对 ID 含 `q6_k` → 再执行 checklist。

**Environment：CONDITIONAL**（模型/磁盘 OK；server 当前 down）。
