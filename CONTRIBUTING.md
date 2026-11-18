# CONTRIBUTING — VAM-Coder（内部整理 / 未来开源准备）

状态：准备稿 · **不构成开源发布许可**

## 1. 冻结数据红线

1. 禁止修改/覆盖/删除：`p1/experiments/**/runs/**`、`tasks*/**`、`manifests/**`、episode、失败日志、冻结 `run_meta`/`code_snapshot`。  
2. 禁止：`git reset --hard`、`git clean`、rebase、squash、filter-repo、强推、删历史分支。  
3. 移动任何可能被程序引用的文件前：记录原路径、新路径、SHA-256、大小；哈希必须一致。  
4. `p1/docs` 根目录预注册路径被硬编码 — **禁止移动**（见 `p1/docs/README.md`）。  
5. 疑似重复文件不得擅自删除。

## 2. 文档与命名

- 正式名：VAM-Coder；V13E（或 V1.3E，选一种对外一致）；VP；F；S1；S2；MOFF。  
- 避免 `final_final2`、`new_latest`；真实版本号可追溯。  
- 历史材料标 ARCHIVE/SUPERSEDED 优先写在索引文档，而非改冻结文件名。  
- 新设计文档放入 `docs/` 或 `p1/docs/<version>/`；冻结预注册仅按 `p1/docs/README.md` 规则放根目录。

## 3. 提交

- 只提交文档/代码变更；大体量实验数据保持 untracked 或按既有 `.gitignore`。  
- 不 force push；不 rewrite history。  
- 提交前自查：是否触碰冻结路径、是否误删、是否引入密钥。

## 4. 密钥与隐私

- 密钥只经环境变量（如 `VAM_API_KEY`/`OPENAI_API_KEY`）；禁止写入仓库。  
- 发现疑似密钥：只报告**位置与类型**，不打印值，不擅自轮换。

## 5. 开源准备（未完成）

- **LICENSE：MIT**（2026-11-18 用户选定，见根目录 `LICENSE`）。  
- 第三方依赖与数据集/模型许可仍需逐项审查后再对外发布（见 `docs/LIMITATIONS.md`）。  
- 绝对路径、个人信息、不可公开数据需清理评估。
