# REPRODUCIBILITY — 复现说明

状态：**PARTIALLY COMPLETED**（依赖清单已有；一键全量复现未封装）

## 环境

- Python ≥ 3.10（实测 3.12.x）
- `requirements.txt`：`tree-sitter`, `tree-sitter-python`, `blake3`, `pytest`（版本钉死）
- 可选：本地 `llama.cpp` / 远程 API（`VAM_API_KEY` / `OPENAI_API_KEY` 环境变量；**禁止**写入仓库）

## 代码入口

```text
产品：src/vam_coder/
实验：p1/scripts/run_p1_v12.py  （及 run_p1_v11.py / run_p1.py）
```

## 冻结复现锚点

| 锚点 | 路径 |
| --- | --- |
| 预注册 | `p1/docs/*.md`（根目录） |
| manifest | `p1/manifests/` |
| run_meta / code_snapshot | 各 `p1/experiments/**/runs/**` |
| 哈希审计 | `experiments/V12-F/reports/V12F_final_validation_and_submission_report.md` §1 |

## 红线

1. 不改冻结数据与预注册路径  
2. 补跑使用**新** run 目录，不覆盖旧数据  
3. 原始配置与超限恢复配置分列  

## 未完成

- LICENSE：**MIT**（根目录 `LICENSE`）；发布前仍需核对第三方与数据集条款。
- Docker/一键脚本全量打包 — **NOT COMPLETED**
