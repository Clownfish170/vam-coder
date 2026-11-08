# Part6 文献核验工作笔记（independent-v1 / V12-F 总报告用）

状态：进行中。规则：**只收录经 API 核验的条目**（arXiv API 返回的 title/authors/published/comment 为准）；
禁止凭记忆写引用。核验日期：2026-11-07（UTC）。检索路径：export.arxiv.org/api（websearch 浏览器路径不可用时的既定替代）。

## 0. 核验方法

- `https://export.arxiv.org/api/query?id_list=...`（按 ID 直取，title 必须与预期一致才采纳）
- `https://export.arxiv.org/api/query?search_query=ti:"..."|all:"..."`（标题/全文检索）
- 记录字段：arXiv ID、标题、第一作者+et al、年份、venue（取 arxiv:comment / journal_ref）、核验日期。
- venue 若 arXiv comment 未给出，标 "preprint (arXiv)"，不编造会议。
- 二次文献转述（如某综述提到 X）不算核验，必须单独核验原文。

## 1. Agent Memory（系统与综述）

| arXiv | 标题 | 作者 | 年 | venue | 备注 |
|---|---|---|---|---|---|
| 2310.08560 | MemGPT: Towards LLMs as Operating Systems | Packer et al. | 2023 | preprint (arXiv) | 分层记忆/虚拟上下文管理 |
| 2304.03442 | Generative Agents: Interactive Simulacra of Human Behavior | Park et al. | 2023 | preprint (arXiv) | 记忆流+反思+检索 |
| 2303.11366 | Reflexion: Language Agents with Verbal Reinforcement Learning | Shinn et al. | 2023 | preprint (arXiv) | 语言反馈进 episodic buffer |
| 2305.16291 | Voyager: An Open-Ended Embodied Agent with LLMs | Wang et al. | 2023 | preprint (arXiv) | **技能库=可执行代码记忆**（与代码记忆最相关） |
| 2404.13501 | A Survey on the Memory Mechanism of Large Language Model based Agents | Zhang et al. | 2024 | preprint (arXiv) | 记忆机制综述 |
| 2605.06716 | From Storage to Experience: A Survey on the Evolution of LLM Agent Memory Mechanisms | Luo et al. | 2026 | ACL 2026 Findings (comment) | Storage→Reflection→Experience 三阶段 |
| 2602.05665 | Graph-based Agent Memory: Taxonomy, Techniques, and Applications | Yang et al. | 2026 | preprint (arXiv) | 图结构记忆综述 |
| 2606.24775 | Are We Ready For An Agent-Native Memory System? | Zhou et al. | 2026 | preprint (arXiv) | 12 系统数据管理视角评测；成本-性能权衡 |
| 2601.01885 | Agentic Memory: Learning Unified Long-Term and Short-Term Memory Management for LLM Agents | Yu et al. | 2026 | ACL'26 SAC Highlight (comment) | LTM/STM 统一进策略 |
| 2610.36918 | TrawMem: Reframing Agent Memory as Task-Oriented Role-Adaptive Workspaces | Zhang et al. | 2026 | preprint (arXiv) | **报告上下文 token 减少 5–13% 量级**（与"降开销"主题相邻） |
| 2605.18421 | EvoMemBench: Benchmarking Agent Memory from a Self-Evolving Perspective | Wang et al. | 2026 | NeurIPS 2026 (comment) | **长上下文基线仍很强；记忆仅在上下文不足时有帮助**（对我们非劣设计的旁证） |

## 2. Long-context（长上下文与退化）

| arXiv | 标题 | 作者 | 年 | venue | 备注 |
|---|---|---|---|---|---|
| 2307.03172 | Lost in the Middle: How Language Models Use Long Contexts | Liu et al. | 2023 | TACL 2023 (comment) | 中段信息利用退化 |
| 2308.14508 | LongBench: A Bilingual, Multitask Benchmark for Long Context Understanding | Bai et al. | 2023 | ACL 2024 (comment) | 含代码补全任务 |
| 2404.06654 | RULER: What's the Real Context Size of Your Long-Context Language Models? | Hsieh et al. | 2024 | COLM 2024 (comment) | 声称窗口 vs 有效窗口 |
| 2607.17937 | When and How Context Rot Appears in Coding Agents: A White-Box Study of Agent Skills in Code Auditing | Xue | 2026 | preprint (arXiv) | **编码 agent 长上下文失败白盒研究**；提到"更小工作集选择"可能有帮助 |
| 2606.29718 | Diagnosing and Mitigating Context Rot in Long-horizon Search | Xia et al. | 2026 | preprint (arXiv) | 上下文管理=降低峰值上下文的 test-time 策略 |
| 2611.04169 | Length Is Cheap, Competition Is Not: Attention Predicts Context Rot in Retrieval | Liu | 2026 | preprint (arXiv) | 竞争性干扰而非长度本身 |

## 3. Context/Prompt 压缩与选择性交付

| arXiv | 标题 | 作者 | 年 | venue | 备注 |
|---|---|---|---|---|---|
| 2310.05736 | LLMLingua: Compressing Prompts for Accelerated Inference of LLMs | Jiang et al. | 2023 | EMNLP 2023 (comment) | token 级压缩，最高 20× |
| 2310.06201 | Compressing Context to Enhance Inference Efficiency of Large Language Models（方法名 Selective Context） | Li et al. | 2023 | EMNLP 2023 (comment) | 50% 上下文压缩、内存-36%/时延-32%；**已核验**（原 ID 猜测错误已纠正） |
| 2609.13154 | Lexical Prompt Compression for LLMs: A Training-Free, Deterministic Pipeline… | Chokshi | 2026 | preprint (arXiv) | 确定性词法压缩 Pareto |
| 2605.26596 | AGORA: Adapter-Grounded Observation-Action Retention for Inference-Free Prompt Compression in LLM Agents | Zhang & Sun | 2026 | preprint (arXiv) | **agent 场景 token 级压缩会破坏动作语法**；步级压缩+结构保底层——与本项目"按结构交付"动机相邻 |

缺口：Selective Context 原文（Li et al., 2023）尚未取得 API 核验记录——继续检索或在报告中标注"未核验不引用"。

## 4. RAG

| arXiv | 标题 | 作者 | 年 | venue | 备注 |
|---|---|---|---|---|---|
| 2005.11401 | Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | Lewis et al. | 2020 | NeurIPS 2020 (comment) | RAG 原始论文（首次 ID 2005.11035 记错已弃用） |
| 2312.10997 | Retrieval-Augmented Generation for Large Language Models: A Survey | Gao et al. | 2023 | ongoing work (comment) | Naive/Advanced/Modular RAG 综述（**已核验**） |

## 5. Coding Agents（含上下文获取）

| arXiv | 标题 | 作者 | 年 | venue | 备注 |
|---|---|---|---|---|---|
| 2310.06770 | SWE-bench: Can Language Models Resolve Real-World GitHub Issues? | Jimenez et al. | 2023 | ICLR 2024 (comment) | 真实 issue 修复基准 |
| 2405.15793 | SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering | Yang et al. | 2024 | preprint (arXiv) | ACI 界面设计影响 agent 表现 |
| 2404.05427 | AutoCodeRover: Autonomous Program Improvement | Zhang et al. | 2024 | ISSTA 2024 (comment) | AST 结构化检索上下文 |
| 2407.16741 | OpenHands: An Open Platform for AI Software Developers as Generalist Agents | Wang et al. | 2024 | ICLR 2025 (comment) | 通用 agent 平台 |
| 2602.05892 | ContextBench: A Benchmark for Context Retrieval in Coding Agents | Li et al. | 2026 | preprint (arXiv) | **过程导向上下文检索评测**（recall/precision/efficiency）；脚手架收益边际 |
| 2607.24882 | Agent Retrieval Bench: Evaluating Repository Context Retrieval for Coding Agents | Qin & Xie | 2026 | preprint (arXiv) | 文件级仓库上下文检索基准 |
| 2606.07297 | SWE-Explore: Benchmarking How Coding Agents Explore Repositories | Zhang et al. | 2026 | preprint (arXiv) | 仓库探索/行级定位评测 |
| 2606.11864 | CORE-Bench: A Comprehensive Benchmark for Code Retrieval in the Era of Agentic Coding | Zhang et al. | 2026 | EMNLP 2026 Main (comment) | 需求驱动仓库检索 |
| 2511.13998 | LoCoBench-Agent: An Interactive Benchmark for LLM Agents in Long-Context Software Engineering | Qiu et al. | 2025 | preprint (arXiv) | **多轮长上下文 SWE agent 基准**（10K–1M token、工具效率、理解-效率权衡） |

## 6. KV Cache / 服务端复用（与本项目边界：不主张 KV 显存收益）

| arXiv | 标题 | 作者 | 年 | venue | 备注 |
|---|---|---|---|---|---|
| 2309.06180 | Efficient Memory Management for LLM Serving with PagedAttention | Kwon et al. | 2023 | SOSP 2023 (comment) | vLLM；KV 分页与跨请求共享 |
| 2312.07104 | SGLang: Efficient Execution of Structured Language Model Programs | Zheng et al. | 2023 | preprint (arXiv) | RadixAttention 前缀 KV 复用 |
| 2311.04934 | Prompt Cache: Modular Attention Reuse for Low-Latency Inference | Gim et al. | 2023 | MLSys 2024 (comment) | 注意力状态模块级复用 |
| 2405.16444 | CacheBlend: Fast LLM Serving for RAG with Cached Knowledge Fusion | Yao et al. | 2024 | preprint (arXiv) | 非前缀 KV 复用+选择性重算保质量 |
| 2306.14048 | H2O: Heavy-Hitter Oracle for Efficient Generative Inference of LLMs | Zhang et al. | 2023 | preprint (arXiv) | KV 逐出策略 |
| 2309.17453 | Efficient Streaming Language Models with Attention Sinks | Xiao et al. | 2023 | ICLR 2024 (comment) | StreamingLLM |
| 2404.14469 | SnapKV: LLM Knows What You are Looking for Before Generation | Li et al. | 2024 | preprint (arXiv) | KV 压缩 |
| 2605.24022 | Adaptive KV Cache Reuse for Fast Long-Context LLM Serving (CacheTune) | Li et al. | 2026 | preprint (arXiv) | **非前缀复用的语义一致性恢复**（与"复用必须验证"主题相邻） |
| 2605.05696 | Irminsul: MLA-Native Position-Independent Caching for Agentic LLM Serving | Ma et al. | 2026 | preprint (arXiv) | agentic 流量内容寻址缓存；output-consistency 评测 |
| 2608.14624 | Learning Agent Execution for KV-Cache Management in Agentic Serving (CacheScout) | Zhang et al. | 2026 | preprint (arXiv) | agent 执行语义引导缓存 |
| 2502.07776 | Auditing Prompt Caching in Language Model APIs | Gu et al. | 2025 | ICML 2025 (comment) | 缓存共享的时序侧信道审计 |
| 2502.03771 | vCache: Verified Semantic Prompt Caching | Schroeder et al. | 2025 | ICLR 2026 (comment) | **带用户定义错误率保证的"已验证缓存"**（与"可验证"叙事相邻，但对象是语义缓存命中，非上下文交付） |

## 7. Memory 评测基准

| arXiv | 标题 | 作者 | 年 | venue | 备注 |
|---|---|---|---|---|---|
| 2402.17753 | Evaluating Very Long-Term Conversational Memory of LLM Agents (LoCoMo) | Maharana et al. | 2024 | preprint (arXiv) | 35 session 长程对话记忆 |
| 2410.10813 | LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory | Wu et al. | 2024 | ICLR 2025 (comment) | 5 类核心记忆能力；长上下文也掉 30% |
| 2605.12493 | LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues | Wu et al. | 2026 | preprint (arXiv) | 环境经验记忆；coding-agent 取证方式 |

## 8. 创新性定位（供总报告 Part6/Part7，事实与推论分开写）

**事实（有上表条目支撑）**：
1. 服务端 KV 复用（vLLM/SGLang/PromptCache/CacheBlend 等）优化的是 prefill 延迟与显存，且 CacheBlend/Irminsul 等明确以"复用后质量/输出一致性"为约束——对象是推理系统，不是 agent 的上下文交付决策。
2. Coding agent 的上下文*获取*在 2026 年已成为独立评测对象（ContextBench、Agent Retrieval Bench、SWE-Explore、CORE-Bench），度量检索 recall/precision/效率与探索行为；均为过程/检索评测，不是"结构化记忆+可验证交付+端到端非劣确认性实验"。
3. Agent memory 文献以对话/QA 记忆为主（MemGPT/LoCoMo/LongMemEval 系）；EvoMemBench 显示长上下文基线仍然很强——支持"必须做非劣确认，不能假设记忆必胜"的方法论。
4. 长上下文退化（Lost in the Middle/RULER/context rot 系）与编码 agent 上下文失败（2607.17937）为"选择性交付降开销"提供动机。

**本项目主张（推论，须在报告中标为推论）**：
- 差异点 = 结构化可寻址代码记忆 + 带可见性证明（O′）的选择性交付 + 多轮编码任务上的端到端确认性非劣协议（prompt 降 vs ESR 非劣）三者组合；单点组件均非新（记忆、检索、KV 复用、压缩各自成熟），组合与验证方式是贡献。
- 禁止主张：KV Cache 显存下降（无张量实测）；双 Token 独立收益（未证实）。

## 9. DOI 补充核验（Crossref，2026-11-07）

| 文献 | DOI | 容器 |
| --- | --- | --- |
| Lost in the Middle (2307.03172) | `10.1162/tacl_a_00638` | TACL (2024) |
| LLMLingua (2310.05736) | `10.18653/v1/2023.emnlp-main.825` | EMNLP 2023 |
| Selective Context / Compressing Context (2310.06201) | `10.18653/v1/2023.emnlp-main.391` | EMNLP 2023 |
| PagedAttention (2309.06180) | `10.1145/3600006.3613165` | SOSP 2023 |
| LongBench (2308.14508) | `10.18653/v1/2024.acl-long.172` | ACL 2024 |

说明：ICLR/NeurIPS/COLM 类会议多数无 Crossref DOI，引用时用 arXiv 链接 + 会议名（来自 arxiv comment）。
AutoCodeRover 的 Crossref 查询遇 429 限流，暂以 arXiv 2404.05427 + comment "ISSTA 2024" 为准，需要时再补 DOI。

## 10. 引用 → RQ/主张 映射表

| 论文用途 | 支撑的 RQ/主张/段落 | 引用条目（arXiv ID） |
| --- | --- | --- |
| 动机：长上下文利用退化 | Intro（为何要降上下文开销） | 2307.03172, 2404.06654, 2308.14508, 2607.17937, 2606.29718, 2611.04169 |
| 相关：Agent Memory | Related Work §Memory | 2310.08560, 2304.03442, 2303.11366, 2305.16291, 2404.13501, 2605.06716, 2602.05665, 2606.24775, 2601.01885, 2610.36918 |
| 相关：上下文压缩/选择性交付 | Related Work §Compression | 2310.05736, 2310.06201, 2609.13154, 2605.26596 |
| 相关：RAG | Related Work §RAG | 2005.11401, 2312.10997 |
| 相关：Coding agent 与上下文获取 | Related Work §Coding Agents | 2310.06770, 2405.15793, 2404.05427, 2407.16741, 2602.05892, 2607.24882, 2606.07297, 2606.11864, 2511.13998 |
| 边界：KV 复用（我们不主张的部分） | Related Work §KV Reuse + Limitations | 2309.06180, 2312.07104, 2311.04934, 2405.16444, 2306.14048, 2309.17453, 2404.14469, 2605.24022, 2605.05696, 2608.14624 |
| 边界：缓存一致性/可验证缓存 | Related Work §Verifiable/Consistency | 2502.03771, 2502.07776 |
| 方法论：非劣确认的必要性 | Setup/Stats rationale | 2605.18421（长上下文基线仍强）, 2410.10813, 2402.17753, 2605.12493 |
| 与 VSO 的机制差异论证 | §8 创新性比较 | 对照 2502.03771（语义缓存错误率保证）、2502.07776（缓存审计）、2605.24022/2605.05696（KV 复用一致性）——对象均为推理缓存，非"最终消息可见性证明" |

## 11. 待办

- [x] Selective Context 原文核验 → 2310.06201（EMNLP 2023）
- [x] RAG 综述核验 → 2312.10997（Gao et al.）
- [x] coding agent 综述 → 未检索到合适综述；改用基准论文（ContextBench/ARB/SWE-Explore/CORE-Bench/LoCoBench-Agent）覆盖该领域
- [x] 关键已发表条目 Crossref DOI（§9 表；其余以 arXiv 正式链接为准）
- [x] 引用与 RQ 的映射表（§10）
- [ ] 投稿前：按目标期刊格式核对 DOI/正式链接完整性（Part7 时按候选期刊要求处理）
