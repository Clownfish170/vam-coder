# VAM-Coder — Repository Structure

旗舰研究对象：**V13E**（V1.3E）  
演进主线：V1.0 → V1.1 → V1.2F → V1.3E  
双 Token：探索过程，**不是**最终核心创新。

## 顶层目录

| 目录 | 职责 |
| --- | --- |
| [development/](development/README.md) | 架构研发与版本演进（仅真实存在的版本） |
| [src/](src/README.md) | **唯一**可运行产品代码入口（`vam_coder`） |
| [experiments/](experiments/README.md) | 独立实验体系索引（物理 run 见各 README 的 canonical path） |
| [manuscript/](manuscript/README.md) | 论文、图表、参考文献、补充材料 |
| [docs/](docs/README.md) | 总览、演进、术语、复现、局限 |
| [scripts/](scripts/README.md) | 通用工具脚本 |
| [archive/](archive/README.md) | 历史材料、归档包、服务日志 |

## 关键约定

1. **冻结数据**在 `p1/experiments/**`、`p1/tasks*`、`p1/docs` 根目录、`p1/manifests` — **禁止移动/改写**。
2. 实验 harness 在 `p1/scripts/`（非产品代码）；产品代码仅 `src/vam_coder/`。
3. 术语见 [docs/GLOSSARY.md](docs/GLOSSARY.md)（O′→VP 映射；不改历史原文）。
4. 结构重组映射：`../VAM_CODER_RESTRUCTURE_MAPPING.tsv` 或见 `VAM_CODER_REPOSITORY_STRUCTURE_REPORT.md`。

## 入口文档

- 架构总览：[docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md)
- V13E：[docs/ARCHITECTURE_V13E.md](docs/ARCHITECTURE_V13E.md)
- 演进：[docs/DEVELOPMENT_HISTORY.md](docs/DEVELOPMENT_HISTORY.md)
- 实验索引：[docs/EXPERIMENT_INDEX.md](docs/EXPERIMENT_INDEX.md)
- 复现：[docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md)
- 局限：[docs/LIMITATIONS.md](docs/LIMITATIONS.md)
