# LIMITATIONS — 局限性（写作必保留）

状态：**ACTIVE**

1. **双 Token** 独立贡献未证实（`dualtoken_report.md`：H-B/H-C 不支持）；不得写成核心创新。  
2. **cached_tokens ≠ KV 显存**；无显存实测。  
3. **VP 边界**：不声称发现全部相关文件；不声称消除全部 TOCTOU。  
4. **S2** 为启发式，非形式化证明。  
5. **P1_TRANSFER**：10 实例子集、本地 Docker FAIL_TO_PASS，**非**官方 SWE-bench leaderboard；**不取代** V13E 主实验。  
6. P1 任务集族依赖 / 有效独立设计 < 题面数（见 V12F 报告 D8）。  
7. ESR 地板与生成非确定性 → 聚类 + 非劣界，不作轻率优效主张。  
8. 开源许可与数据集再分发条款 **NEEDS REVIEW**。

证据入口：`docs/APPENDIX_INDEX.md` · `experiments/*/README.md`
