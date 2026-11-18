# VAM_CODER_V13E_FINAL_CLEANUP_REPORT

**交付物（唯一）：** `VAM_CODER_V13E_FINAL_CLEANUP_REPORT.md`  
**项目：** VAM-Coder · 旗舰 **V13E**  
**演进主轴：** V1.0 → V1.1 → V1.2F → V1.3E  
**执行日期：** 2026-11-18  
**模式：** 只读盘点 + 安全文档新增（**未**改代码逻辑 / 实验数据 / 冻结配置 / 原始日志）

**状态标记：** `COMPLETED` / `PARTIALLY COMPLETED` / `NOT COMPLETED` / `NEEDS USER APPROVAL`

---

## 1. 整理前后状态

### 1.1 整理前（盘点）

| 项 | 状态 | 说明 |
| --- | --- | --- |
| 工作区 | `D:\Demo\DynaMem` | 含 `vam-coder/` Git 仓库、顶层手稿/分析、`research/`、`v06_figs/` |
| Git 分支 | `p1/v1.1`（HEAD `9781a6d` 清理前快照）；另有 `main`、`p1/v0.2`；`stash@{0}` | **COMPLETED**（只读记录） |
| 未跟踪 | 16 项实验/任务目录（v13a/b/d/e、tasks_* 等） | **COMPLETED**（保留，靠文件备份保护） |
| 已修改（快照时） | 9 个 v12/v11 脚本与测试 | 已纳入 `9781a6d` |
| 冻结路径 | `p1/docs` 根目录预注册被硬编码（`p1/docs/README.md` 明确禁止移动） | **COMPLETED**（遵守，零移动） |
| 备份 | `D:\Demo\DynaMem_BACKUP_20261117\`（约 4,890 MB / 716,435 文件；SHA256 抽检 6/6） | **COMPLETED** |
| 冻结数据体量 | `p1/experiments` 多 run；`p1/results/runs` 等被 `.gitignore` 排除大日志 | **COMPLETED**（盘点） |

### 1.2 整理后

| 项 | 状态 | 说明 |
| --- | --- | --- |
| 实验/任务/manifest/原始日志 | **未改动** | **COMPLETED** |
| `p1/docs` 根目录冻结文件 | **未移动、未改名** | **COMPLETED** |
| 新增规范文档 | `vam-coder/docs/**` 六件套 + `docs/README.md` | **COMPLETED** |
| 仓库级说明 | `CHANGELOG.md`、`CONTRIBUTING.md` | **COMPLETED** |
| 顶层手稿/图/zip | **原位保留**（路径引用未全部核验，不迁移） | **PARTIALLY COMPLETED**（索引完成，物理归置未做） |
| 重命名冻结文件 | **无** | **COMPLETED**（按红线执行） |
| Git 提交（文档） | 见 §7 | **COMPLETED** |

---

## 2. 目录结构（现状）

### 2.1 仓库 `vam-coder/`（整理后）

```text
vam-coder/
  README.md, PATCH_NOTES*.md, V12F_final_validation_and_submission_report.md
  CHANGELOG.md, CONTRIBUTING.md          ← 新增
  requirements.txt, pytest.ini, .gitignore
  docs/                                  ← 新增规范区
    README.md
    terminology/GLOSSARY.md
    architecture/ARCHITECTURE_V13E.md
    mechanisms/MECHANISM_VISIBILITY_PROOF.md
    development-history/DEVELOPMENT_HISTORY.md
    methodology/EXPERIMENT_INDEX.md
    supplementary/APPENDIX_INDEX.md
  src/vam_coder/                         ← 核心库（未改）
  scripts/                               ← 顶层脚本（未改）
  tests/                                 ← 单测（未改）
  config/, results/, logs/, state/       ← 未改（logs/state 为 ignore 运行时）
  p1/
    docs/                                ← 冻结预注册根 + 版本子目录（未移动）
    scripts/{v11,v12,cr}/                ← 机制代码（未改逻辑）
    experiments/                         ← 全部实验（只读）
    tasks*/                              ← 全部任务集（只读）
    manifests/, results/, tests/
```

### 2.2 工作区顶层 `D:\Demo\DynaMem`（原位保留）

```text
*.md/*.json/*.docx/*.zip/*.bundle        ← 手稿、分析、归档（索引见附录）
v06_figs/                                ← 论文曲线图
research/                                ← 调研笔记
vam-coder/                               ← 主仓库
vam-coder_history.bundle                 ← 历史 bundle（只读）
llama.cpp/, models/                      ← 运行环境（非本清理对象）
```

### 2.3 备份

```text
D:\Demo\DynaMem_BACKUP_20261117\
  vam-coder/ research/ v06_figs/ 顶层文件 RECOVERY_README.txt BACKUP_VERIFY.txt ...
```

---

## 3. 重命名 / 移动清单

| 动作 | 原路径 | 新路径 | SHA-256 前后 | 结果 |
| --- | --- | --- | --- | --- |
| **无移动/重命名** | — | — | — | **COMPLETED**（零冻结路径变更） |
| 仅新增 | — | `vam-coder/docs/**` 等 | 新文件，无“前后哈希” | **COMPLETED** |

**决策依据：**

1. `p1/docs/README.md`：根目录被预注册/run_meta/核验脚本硬编码。  
2. 顶层手稿与实验内副本（如 `P1_TRANSFER_PROTOCOL_AND_RESULTS.md` 双份）引用关系未完全核验 → **不删、不并、不迁**。  
3. 用户红线：路径引用无法保证时保留原位；不得擅自删重复文件。

**ARCHIVE/SUPERSEDED 标注（写在索引，不改文件名）：**

| 材料 | 标记 | 位置 |
| --- | --- | --- |
| dualtoken 补记 v1 | SUPERSEDED（由 v2 取代任务集条款） | v2 文档头部 + DEVELOPMENT_HISTORY |
| V1.0 设计文档 | ARCHIVE | DEVELOPMENT_HISTORY §1 |
| 探索支线 CR/ICG/VAD | ARCHIVE/非核心 | DEVELOPMENT_HISTORY §4 |

---

## 4. 哈希验证

| 验证 | 方法 | 结果 | 状态 |
| --- | --- | --- | --- |
| 备份完整性 | `BACKUP_VERIFY.txt` SHA256 抽检 | 6/6 MATCH（脚本、.gitignore、手稿、bundle、zip） | **COMPLETED** |
| 备份结构 | 实验目录 28=28；tasks* 9=9；关键路径 19 OK | FAIL_COUNT=0 | **COMPLETED** |
| 源数据未损 | 备份后抽查源路径仍 OK | OK | **COMPLETED** |
| 整理前后冻结文件哈希 | 本次未移动冻结文件 | 无需前后对照；Git 快照 `9781a6d` 可回退文档层 | **COMPLETED** |
| 程序读取路径 | 未改 scripts/tasks/experiments 相对布局 | 未破坏 | **COMPLETED** |
| 全量逐文件哈希清单 | 71 万文件全量哈希表 | 未生成（时间成本高） | **NOT COMPLETED**（可选，见未完成事项） |

---

## 5. 术语表（摘要）

完整表：`vam-coder/docs/terminology/GLOSSARY.md`

| 正式写法 | 定义 | 旧名映射 |
| --- | --- | --- |
| VAM-Coder | 项目名 | vam_coder |
| **V13E**（V1.3E） | 最终旗舰 | V1.3E / v13e / SAH 主臂 |
| **VP** | Visibility Proof | **O′**（仅新文档映射，不改历史） |
| **F** | Selective Context Delivery | 臂 F / V1.2F 基座 |
| **S1** | Verified History Projection | SAH project / 历史折叠 |
| **S2** | 义务账本（**辅助启发式**） | SAH ledger |
| **MOFF** | Memory Off 全量仓库上下文管理策略 | memory_off；**非外部 Coding Agent** |
| P1_TRANSFER | 真外部扩展验证 | 不取代 V13E 主实验 |
| 双 Token | 探索过程 | 非最终核心创新 |

**术语冲突检查：** **COMPLETED** — 旧名集中于历史预注册/设计稿；新六件套统一正式写法；未改冲突原文。

---

## 6. 附录归档与论文材料

索引：`vam-coder/docs/supplementary/APPENDIX_INDEX.md`

| 类别 | 材料 | 状态 |
| --- | --- | --- |
| 架构/流程 | ARCHITECTURE_V13E、MECHANISM_VP、v1.2 架构文、v13e 设计稿 | **COMPLETED**（索引+新建文字版） |
| 版本演进 | DEVELOPMENT_HISTORY | **COMPLETED** |
| 数学/伪代码 | method_formulation + 模块 docstring | **COMPLETED**（索引） |
| 任务/配置 | EXPERIMENT_INDEX | **COMPLETED** |
| 统计/故障注入 | V12F 总报告、STATS_*、VSO、稳健性审计 | **COMPLETED**（索引） |
| 双 Token 取舍 | dualtoken_report（H-B/C 不支持） | **COMPLETED** |
| 局限性 | §8 局限清单写入 APPENDIX_INDEX | **COMPLETED** |
| 位图架构图 | 无独立 V13E 架构 PNG | **PARTIALLY COMPLETED**（文字+可重绘；未生成新图以免不一致） |
| 手稿 docx/md/figs | 顶层原位 | **PARTIALLY COMPLETED**（已索引，未迁入 repo） |

---

## 7. Git 历史保护

| 检查/动作 | 结果 | 状态 |
| --- | --- | --- |
| 只读 status/log/branch/stash | 已记录 | **COMPLETED** |
| 预清理快照提交 | `9781a6d`（32 文件，代码/文档/测试） | **COMPLETED** |
| 文档规范提交 | 见下方 HEAD | **COMPLETED** |
| reset/clean/rebase/squash/filter-repo/强推 | **未执行** | **COMPLETED** |
| 删除历史分支/stash | **未执行**；`main`/`p1/v0.2`/`stash@{0}` 保留 | **COMPLETED** |
| 发布 GitHub | **未执行** | **COMPLETED** |
| 陈旧 `index.lock` | 已确认无 git 进程后清除（非历史改写） | **COMPLETED** |

**清理后 Git 状态：**

- 分支：`p1/v1.1`
- 快照提交：`9781a6d`（预清理代码/文档）
- 文档提交：**`f523967`** `docs(v13e): 术语/架构/VP/演进/实验/附录规范索引与 CHANGELOG/CONTRIBUTING`（9 files, +526）
- untracked：原实验/任务目录（保持，未入库）

---

## 8. 开源风险

| 项 | 发现 | 状态 |
| --- | --- | --- |
| LICENSE | **仓库无 LICENSE 文件** | **NEEDS USER APPROVAL**（不得自选许可证） |
| 第三方 Python 依赖 | `requirements.txt`：tree-sitter、tree-sitter-python、blake3、pytest（版本钉死） | **PARTIALLY COMPLETED**（已列；各包 LICENSE 未逐项归档） |
| 数据集 | SWE-bench Lite 等引用；HF revision 已在协议披露 | **NEEDS USER APPROVAL**（再分发条款） |
| 模型/endpoint | DeepSeek / Qwen API 使用 | **NEEDS USER APPROVAL**（条款与密钥管理） |
| 密钥扫描 | 未见仓库内明文 API key；仅有 `os.environ` 读取 `VAM_API_KEY`/`OPENAI_API_KEY`；实验 prompt 中的 “password/Bearer” 为**基准仓源码噪音** | **COMPLETED**（报告位置与类型，未打印值） |
| 绝对路径 | 大量 `D:\Demo\...` 出现在**冻结 run 日志/eval_output**（不可改）；代码侧以相对路径为主 | **PARTIALLY COMPLETED**（披露；开源前需评估日志是否入库） |
| 个人信息 | 未发现明显账号/手机号模式（抽查） | **PARTIALLY COMPLETED**（非穷尽） |
| 不可公开数据 | 本地 run、模型输出、可能含内部 issue 文本 | **NEEDS USER APPROVAL** |
| 安装/复现说明 | 有 `requirements.txt`、README、协议文档 | **PARTIALLY COMPLETED**（缺完整一键复现） |
| 发布 | 未发布 | **COMPLETED**（按要求只准备） |

---

## 9. 未完成事项 / 材料缺口

| 事项 | 标记 |
| --- | --- |
| 仓库 LICENSE 选定与第三方许可证清单 | **NEEDS USER APPROVAL** |
| 顶层手稿/图/zip 是否迁入 `manuscript/` 或 `supplementary/` | **NEEDS USER APPROVAL**（路径引用风险） |
| 71 万文件全量 SHA256 清单 | **NOT COMPLETED**（可选） |
| V13E 架构正式位图（出版级） | **NOT COMPLETED**（可从文字版重绘） |
| SWE-bench / 模型数据许可法律复核 | **NEEDS USER APPROVAL** |
| 将 untracked 大体量实验纳入 Git LFS 或发布策略 | **NEEDS USER APPROVAL** |
| 旧名 O′ 在**代码字符串/注释**中的逐步替换 | **NOT COMPLETED**（有意保留，避免破坏历史与测试） |

---

## 10. 最终状态总表

| 任务 | 状态 |
| --- | --- |
| 盘点仓库与冻结数据 | **COMPLETED** |
| Git 状态 / 大文件 / 敏感信息只读检查 | **COMPLETED** |
| 路径与哈希对照（冻结移动） | **COMPLETED**（零移动 + 备份抽检） |
| 目录与命名设计（按实际情况，不机械套用） | **COMPLETED** |
| 术语冲突检查与 GLOSSARY | **COMPLETED** |
| 论文附录检查与 APPENDIX_INDEX | **PARTIALLY COMPLETED**（缺位图/手稿迁移） |
| Git 与开源风险检查 | **PARTIALLY COMPLETED**（LICENSE 等待批准） |
| 安全整理文档文件 | **COMPLETED**（只新增规范区） |
| 验证哈希 / 程序路径 / Git / 重要提交 | **COMPLETED** |
| 生成本报告 | **COMPLETED** |
| 禁止破坏数据 / 改历史 | **COMPLETED**（全程遵守） |

---

## 11. 证据与规范文档入口

| 文档 | 路径 |
| --- | --- |
| 术语 | `vam-coder/docs/terminology/GLOSSARY.md` |
| V13E 架构 | `vam-coder/docs/architecture/ARCHITECTURE_V13E.md` |
| VP 机制 | `vam-coder/docs/mechanisms/MECHANISM_VISIBILITY_PROOF.md` |
| 版本演进 | `vam-coder/docs/development-history/DEVELOPMENT_HISTORY.md` |
| 实验索引 | `vam-coder/docs/methodology/EXPERIMENT_INDEX.md` |
| 附录索引 | `vam-coder/docs/supplementary/APPENDIX_INDEX.md` |
| 恢复说明 | `D:\Demo\DynaMem_BACKUP_20261117\RECOVERY_README.txt` |
| 备份校验 | `D:\Demo\DynaMem_BACKUP_20261117\BACKUP_VERIFY.txt` |

---

**结论：** 冻结数据与 Git 历史完好；规范文档与索引已建立；开源发布与手稿物理归置需你确认后下一步执行。  
**报告状态：** `COMPLETED`（本交付物）
