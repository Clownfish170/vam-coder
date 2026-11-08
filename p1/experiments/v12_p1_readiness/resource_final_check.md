# 资源最终检查

| 项 | 状态 | 证据 |
| --- | --- | --- |
| 模型文件 | **PASS**（存在；P0 已用） | `D:/Demo/DynaMem/models/qwen2.5-coder-1.5b-instruct-q6_k.gguf` |
| 磁盘 | **PASS** ~34 GB free | shutil D: |
| llama-server 本门禁时 | **WARNING** `/v1/models` 超时 | 门禁 curl；P0 曾 PID 4212 |
| 预计请求 | **1008**（P1） | prereg§4 |
| 预计时长 | **约 1–4 小时** 串行 | resource_estimate（P1 review） |
| 并行 | **禁止**多实验并行 | 预注册 parallel=1 |
| 中断 | 可停；禁止伪造完成 | 预注册排除规则 |
| 自动重试 | **无**（计数安全） | runner 无 retry loop |

## P1 启动前必须

1. 启动 llama-server 并 **200** 健康检查  
2. 确认无其他任务占用 8080  

**Resource Readiness：CONDITIONAL**（server 当前未验证在线）。
