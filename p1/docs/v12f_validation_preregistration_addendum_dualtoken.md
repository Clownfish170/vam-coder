# 预注册补记：双 Token 独立消融（Static Representation × Symbolic Addressing）

状态：**冻结——本声明写于任何 A/B/C/D 实验请求之前；禁止事后修改机制定义与指标。**  
日期：2026-11-07 · 排产优先级 #3  
（补记仅新增专项实验；不改动 v1 冻结条款，不替代 P1/P2/P3-A/VSO 已有结论。）

---

## 1. 科学问题与机制定义（双 Token 的正确口径）

> **内部静态可复用表示（Static Reusable Representation, SRR）** 与 **外部符号 ID 寻址记忆（Symbolic ID Addressing, SA）** 是否各自产生独立的上下文收益？动态信息是否仍被正确交付？

- **不是** prompt/completion 成本归因（那是辅助统计，见 §5）。
- 双 Token 指上述两种"跨轮次承载信息的机制"，独立贡献 = 单变量对照下的效应。

## 2. 四组设计（A/B/C 单变量；D 系统参照）

**全局固定（四组一致）**：任务集 = `p1/tasks_p1_validation`（已冻结48题）；模型 = `deepseek-v4.1-flash-1017`；max_tokens=2048；temperature=0/seed=0；history=keep；d=2；K_max=8；R=5；**VSO 安全条件固定**（pre_send 强制校验、E/C 禁 O′、must/ET 强制 Full、INSUFFICIENT 门闩全部启用）；相关性判定（task-aware r 分数）四组相同——**改变的只有"相关非目标内容如何跨轮承载"**。

| 组 | 机制 | 实现（全部测试侧/既有开关） |
| --- | --- | --- |
| **A — Inline Full Context** | 每轮把相关非目标内容**原文内联重发**，不做静态压缩、不做符号寻址 | 配置 = `non_target_related=full` + `o_prime=False`（既有 `--no-oprime` 开关；禁止省略 → 每轮全量重发）；架构标识 `dualtoken_A_inline_full_context` |
| **B — Symbolic Addressing only** | 相关非目标文件不内联原文：仅投递**符号 ID 行**；指令命中的符号在装配时按 ID 解析并投递**函数级源码切片** | orchestrator 进程内包装 `assemble_v12`（VSO Phase2 同款测试侧注入）；`dualtoken_B_symbolic_addressing` |
| **C — Static Rep + Symbolic ID** | 稳定信息 = **静态紧凑表示**（`file::sym` 签名行，跨轮可复用、O′ 可整文件省略）；指令命中符号按 ID 投递完整源码 | 同一包装器的 C 模式；`dualtoken_C_static_rep_plus_symbolic_id` |
| **D — Full V12-F** | 完整系统原样（基准参照，**非单变量组**） | 无包装（零改动），`vam_coder_v1.2_F` |

**动态信息铁律（四组共同断言）**：文件在本步被修改后，下一步上下文必须反映**当前**内容——A 每轮重发自然满足；B 靠装配时按 ID 从当前工作区取源；C 靠命中符号的当步取源；D 走既有链路。dry-run/分析中对 A/B/C 各抽取"step1 修改 → step2 上下文含新值"断言（每组≥3 例，机器可检）。

**信息源一致性**：B/C 的符号解析目标 = 与 D 相同的工作区/符号索引（同源），不引入外部检索器；"检索策略"（相关性打分、must 闭包、目标解析）四组同一套代码。

## 3. 实验规模与执行

- **48 tasks × 4 arms × R=5 = 960 episodes**（≈5,500–5,800 请求；dry-run 预算估算后写入 run_meta，S5 = 2× 估算）。
- 随机化 seed = **20261110**（仅顺序）；bootstrap seed=20261102、cluster=task_id（沿用冻结统计口径）。
- 断点续跑（沿用 execution_log 模式）；随机化、run_meta、冻结哈希核验先于首个请求。
- 预算/成本：按 P1/P2 同量级 flash 调用估算（全场 ≈3–4M tokens），**无新模型服务**。
- 后台执行；失败分类沿用 rev3 §4.5。

## 4. 主要假设（预注册）

- **H-B**：`dualtoken_B_symbolic_addressing` 相对 D 的 prompt/episode 显著更低（符号寻址省内联），且 ESR 非劣（界值沿用 −12pp，同 v1）。
- **H-C**：`dualtoken_C_static_rep_plus_symbolic_id` 相对 D 的 prompt/episode 显著更低，且 ESR 非劣（−12pp）。
- **H-AB**（独立性）：C − B 的配对差可分离"静态表示"与"寻址"的各自贡献方向（C 含两者、B 仅寻址；同信息源下 Δ 归因于静态表示的增量）。
- A 为机制对照（全量重发上界）：A − D 的 Δprompt 量化"不做任何跨轮复用"的成本。
- 判定不依赖 p 值单独成立：效应量 + 95% CI 为主；两主比较（B−D、C−D）Holm 校正；A−D、C−B 为次要/机制比较。

## 5. 指标（双 Token 专项 + 通用）

**专项（四组同口径）**：
| 指标 | 操作定义 |
| --- | --- |
| Peak Context Tokens | 单 episode 内 max(step prompt_tokens) |
| Context Growth Rate | task×arm 内 prompt_tokens 对 step 序号的 OLS 斜率（tok/step），按组汇总均值 |
| Redundant Token Ratio | Σ(步 context 中与先前已发送内容同 sha 的块 tokens) / Σ(context tokens)（复用即冗余重发的反面；A 应最高、B 最低） |
| Retrieval Overhead | 寻址开销 = Σ(SYMBOL/签名/ID 行 tokens) + 指令命中符号源码 tokens（B/C 专属，A/D=0） |
| Latency | t_model_ms / t_step_ms 已有字段 |

**通用**：prompt/completion/total 分列（**仅组内比较**；四组同 tokenizer 同模型可比）、ESR/SPR、**CMR**（沿用 CIRE 口径：144 个预声明信息点在该步 user.context/可见面的送达率，`redundant_in_instruction` 分解）、TPAE/TPSE。

**不做的解释**：不得把组间差异表述为 KV Cache 显存收益；不得跨模型合并绝对 token。

## 6. 验证门（实现后、正式跑前，全部通过才开跑）

1. dry-run 断言：A 的 context 含相关非目标**原文块**且无 REUSE 省略；B 的 context **无**相关非目标原文块、含 `SYMBOL`/源码切片行；C 含签名行与命中符号源码；D 与 P1 的 F 形态逐字节同构（除臂名头部已统一为 `[ctx]`）。
2. 动态交付断言（§2 末）：A/B/C 各≥3 例。
3. 安全不变量：四组 INSUFFICIENT/DHO/pre_send 违规=0（dry-run 全量 + 实跑监控）。
4. 每组随机抽 1 集真模型 smoke（FILE 协议、usage 字段）后放行全量。

## 7. 边界与诚实条款

- A/B/C 的任何差异**不得**归因于 VSO（VSO 四组固定；其独立贡献已由 VSO 专项单独验证）。
- B/C 为 orchestrator 侧策略包装（**生产代码零修改**；若实现发现必须改 `p1/scripts`/`src/` → 停下报告，按总任务约束处理）。
- 本补记不替代 Part2 独立任务集确认性实验；双 Token 结论标注"机制专项、P1 任务集"。
- 探索/确认分栏：本实验为**确认性机制专项**（假设 H-B/H-C 预注册在先）；任何事后新增假设标探索性。
