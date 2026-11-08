# P1 正式执行前检查清单

授权执行 **之前** 逐项打勾。未勾选不得开跑。

## A. 冻结与 Git

- [ ] Branch `p1/v1.1`，HEAD `155f934bc6c565bd304b2b7438259d592bc348c8`
- [ ] stash@{0} 未动
- [ ] V1.0 三项 SHA 与 `git_integrity_report.md` 一致
- [ ] r2.2 七文档 SHA 一致
- [ ] 无未授权 code/任务/预注册修改

## B. 环境

- [ ] Q6_K 模型文件存在
- [ ] llama-server：`/v1/models` **200**（P1 当日）
- [ ] `-c 8192 --parallel 1`
- [ ] 磁盘可用 ≥ 5GB
- [ ] seed=0 temperature=0 max_tokens=1024 history=keep
- [ ] closure_depth=2 Kmax=8

## C. 方案

- [ ] 预注册 r2.2 哈希锁定
- [ ] P1 范围：24 任务 × A,B,D,E,F,G,H × R=3 ≈ **1008** 请求
- [ ] 新 `randomization_manifest`（seed 写明）
- [ ] 输出根独立（不覆盖 P0/`v1_formal`）

## D. 数据采集

- [ ] 每 episode 独立 workspace
- [ ] （若授权）`workspace_pre_manifest` 在首次请求前写入
- [ ] （若授权）post + diff 写入
- [ ] 每步保存 context/messages/pre_send/audit/response/eval/result
- [ ] 失败分类字段可写

## E. 安全

- [ ] `should_call_model` 门闩在位（代码审查）
- [ ] 单测 181 / gate 10 已绿
- [ ] 报告用 **VP/vproof** 术语
- [ ] 禁止自动重试刷成功

## F. 统计

- [ ] 可从 per_step 重算 ESR/SPR/TPAE/TPSE/FETC
- [ ] 零成功 TPSE=NA/∞；零失败 FETC_mean=NA
- [ ] cached_tokens 不当 KV 节省
- [ ] 措辞不含“显著优于/证明有效”

## G. 授权

- [ ] 用户书面批准 P1 执行
- [ ] 批准文本与样本量/臂一致

---

**本清单不构成授权。**
