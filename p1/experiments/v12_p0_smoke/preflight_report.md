# V1.2-r2.2 P0 Smoke — Preflight（阶段 A）

状态：**只读准备完成**；**未**发送任何模型推理请求（仅 `/v1/models` 健康检查）。  
目录：`p1/experiments/v12_p0_smoke/`

---

## 1. Git / 工作区

| 项 | 值 | 期望 | 结果 |
| --- | --- | --- | --- |
| 分支 | `p1/v1.1` | `p1/v1.1` | **PASS** |
| HEAD | `155f934bc6c565bd304b2b7438259d592bc348c8` | 同 | **PASS** |
| stash | `stash@{0}` GitHub_Desktop | 存在且未 pop | **PASS** |
| v12 相关工作区 | 设计文档/run_p1_v12/v11/v12/tests 均为 `??` 未跟踪 | 与验收时一致（未 commit） | **PASS**（预期） |

---

## 2. 冻结资产 SHA256

| 文件 | SHA256 | 结果 |
| --- | --- | --- |
| `tasks_v1.0.json` | `1f3db0090fd62c8f934ed1271b28d0f955c9763fe2956efb30d2a12179f00339` | **PASS** |
| `formal_runs.csv` | `279d80f8c2a4f9e608395bf891ba91541517193dc7548e9e57dae8bacf9c2375` | **PASS** |
| `p1_v1.0_manifest_20261030.json` | `e82072f4c222e9927762b383a1e344bcd799d5f08c38486665d7eed8cca696df` | **PASS** |

---

## 3. V1.2-r2.2 设计文档 SHA256（验收清单）

| 文件 | SHA256 | 结果 |
| --- | --- | --- |
| architecture | `594a9933df464c8ee91ea2963ff2ede907bc4fd1ab4af08368736be07c6188eb` | **PASS** |
| method | `f52bc5bdfd68af11abba256193cd6681137ff536f67362920d9dc3450af24e4f` | **PASS** |
| prereg | `7d594e1c2b5de063ef75c2bdbaa65e5365607c1651a873b2960fc9b70a7425fc` | **PASS** |
| roadmap | `579ec72dea4fcecd0dbe47f1d55cc8ab973e7d0c8ba2fb3772fdb51d77fa11d5` | **PASS** |
| novelty | `95dbfc36e3f2df4fae358986090b79fcb7885f00800cf1eb1343b3a199331be3` | **PASS**（未改） |
| design_review_response | `f0abd2f6eb184ccae6815974b52b81141b2a93375dfcbd4fbcbc890c540e06e6` | **PASS** |
| change_note | `fbcba7ccbcc2dbf701a6abbaa3e8978997259602a6e2ce96e557674d834a3a12` | **PASS** |

---

## 4. M1–M4 / M3-FIX-01 代码与测试

| 项 | 值 |
| --- | --- |
| 关键代码 | `p1/scripts/v12/*`、`run_p1_v12.py`（`should_call_model` 门闩） |
| 测试 | `pytest p1/tests tests` → **181 passed**（本 preflight 再次执行） |
| 门闩测试 | `test_v12_m3_fix01_gate.py` **10 passed**（同轮） |

**PASS**

---

## 5. 模型与推理服务（对照 prereg）

| 项 | prereg | 实测 | 结果 |
| --- | --- | --- | --- |
| 模型文件 | Qwen2.5-Coder-1.5B-Instruct **Q6_K** | `.../qwen2.5-coder-1.5b-instruct-q6_k.gguf` 存在，1.46GB | **PASS** |
| 服务 | llama-server | PID **4212** `llama-server.exe` | **PASS** |
| endpoint | 127.0.0.1:8080/v1 | `/v1/models` 200，名称含 q6_k | **PASS** |
| context | 8192 | 命令行 `-c 8192` | **PASS** |
| parallel | 1 | `--parallel 1` | **PASS** |
| seed/temp/max_tokens | 0 / 0 / 1024 | **客户端参数**，由 runner 传入（非服务端） | **PASS**（执行时写入 request） |
| history | keep | 执行时 `--history-policy keep` | **PASS**（待执行时确认） |

服务命令行原文：

```text
llama-server.exe -m .../qwen2.5-coder-1.5b-instruct-q6_k.gguf -ngl 99 -c 8192 --parallel 1 --host 127.0.0.1 --port 8080
```

---

## 6. 冻结参数（P0 必须保持）

`d=2` · `Kmax=8` · E/C 强制 FULL · O′ · 请求前 INSUFFICIENT · E/F/G/H 非目标策略（r2.2 §3.0）。

---

## 7. 样本量说明（**非**预注册强制）

prereg **未**单独规定 r2.2 P0 Smoke 的请求条数。  
下表为 **建议方案**（待你批准），**不得**写成“预注册要求”：

| 建议 | 内容 |
| --- | --- |
| 任务 | 8（见 task_mapping.csv） |
| 臂 | E,F,G,H（r2.2；D 为 v1.1 对照，**本 P0 可选**） |
| 重复 | R=1 |
| API 上限 | 8×4×2 步 = **64** 请求（若含 D 则 +16=80） |
| 输出根 | `p1/experiments/v12_p0_smoke/`（新建，不覆盖旧 smoke） |

---

## 8. 阶段 A 结论

| 项 | 结果 |
| --- | --- |
| 环境 / 冻结 / 文档 / 181 tests | **PASS** |
| 模型与 server 参数 | **PASS** |
| 真实 P0 推理 | **未执行**（待阶段 B 批准） |

**等待你审核 `task_mapping.csv` 与建议样本量后，再批准阶段 C。**
