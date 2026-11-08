# Round 3 实验报告：模型换为 deepseek-v4.1-flash-1017（五架构对比）

状态：**完成**。架构一律完整英文标识；模型换用为用户授权变更。
统计：bootstrap seed=20261102、B=10000、cluster=task_id；随机化 seed=20261105（仅顺序）。

---

## 1. 变更与 Preflight

| 项 | 内容 |
| --- | --- |
| 模型 | `deepseek-v4.1-flash-1017` @ `https://maas.qianwenaiapi.com/compatible-mode/v1` |
| 鉴权 | 环境变量 `VAM_API_KEY`（p1_common 新增**可选** Authorization 头；本地无该变量行为不变） |
| 哈希 | SYSTEM_PROMPT `4f591635…`、build_messages `f0b477b0…` **与 rev3 冻结值一致**；p1_common 因传输层变更新 sha256=`b6ce07a3…`（写入 run_meta）；holdout manifest 逐文件复核通过（任务零改动） |
| Preflight | /v1/models 列出模型 ✓；真实请求 200，usage 含 prompt/completion/**cached_tokens**；FILE: 协议可用；holdout 单集 smoke 两步全过 |
| 规模 | 12 tasks × 5 architectures × R=2 = **120 episodes / 240 requests** |
| Token | 累计 P+C = **141,303** < S5=256,000（2× 预估），无 S1–S5 触发 |
| 注意 | completion_tokens **含 reasoning_tokens**（usage.completion_tokens_details 可见）；max_tokens=1024 沿用冻结值 |

## 2. 结果（metrics_summary.csv，n=24 episodes/架构）

| 架构（完整名） | ESR [Wilson 95% CI] | SPR | prompt/ep | TPAE | TPSE | 失败集（episode） |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `vam_coder_v1.2_E` | 83.3%（20/24）[64.2, 93.3] | 0.8333 | **663.2** | 1085.0 | 1302.0 | I01×2, I02×2 |
| `vam_coder_v1.2_F` | **91.7%（22/24）[74.2, 97.7]** | 0.9167 | 702.5 | 1158.9 | **1264.2** | I01×1, D02×1 |
| `vam_coder_v1.3_V13B` | 83.3%（20/24）[64.2, 93.3] | 0.8333 | 702.6 | **1079.9** | 1295.8 | I01×2, I02×2 |
| `memory_off` | 91.7%（22/24）[74.2, 97.7] | 0.9167 | 824.0 | 1251.7 | 1365.5 | I01×1, I02×1 |
| `symbol_full_read` | 91.7%（22/24）[74.2, 97.7] | 0.9167 | 836.5 | 1312.2 | 1431.5 | I01×1, D02×1 |

**模型能力确认为首要瓶颈**：同一任务集、同一五架构，ESR 从 round2 的 0–4.2% 跃至 **83.3–91.7%**。INSUFFICIENT/DHO=0；protocol_violation 出现 **5 步**（见 §4.2）。

## 3. 配对 Bootstrap（关键差值，95% CI）

| 配对 | ΔESR | Δprompt/ep | ΔTPAE |
| --- | --- | --- | --- |
| `vam_coder_v1.3_V13B` − `vam_coder_v1.2_F` | **−8.3pp [−29.2, +8.3]** | +0.1 [−8.6, +6.7] | −79.0 [−166.6, **−1.6**] |
| `vam_coder_v1.3_V13B` − `vam_coder_v1.2_E` | 0 [0, 0] | +39.3 [+2.6, +98.5] | −5.1 [−73.2, +50.8] |
| `vam_coder_v1.3_V13B` − `memory_off` | −8.3pp [−20.8, 0] | **−121.5 [−148.3, −94.5]** | **−171.8 [−210.7, −131.6]** |
| `vam_coder_v1.3_V13B` − `symbol_full_read` | −8.3pp [−29.2, +8.3] | **−134.0 [−166.4, −104.5]** | **−232.4 [−325.6, −144.9]** |
| `vam_coder_v1.2_F` − `vam_coder_v1.2_E` | +8.3pp [−8.3, +29.2] | +39.3 [+2.8, +96.1] | +73.9 [−17.2, +173.0] |

- 相对非 VAM 架构：prompt/TPAE 优势**继续显著**（CI 全负，约 −15~18% TPAE），但 ESR 点估计落后 8.3pp（CI 触 0）。
- V13B vs `vam_coder_v1.2_F`：**prompt 打平（+0.1）**，TPAE 的 −79 **全部来自 completion 侧**（V13B 合计 9,055 vs F 10,953，reasoning/响应长度差），不是注入省出来的——不得解读为注入策略收益。
- ESR 排名（F=memory_off=symbol 91.7% > E=V13B 83.3%）全部 CI 重叠，n=24 不足以定序。

## 4. 关键发现

### 4.1 首次出现"注入内容因果性翻转 ESR"：v13_I02

- `vam_coder_v1.2_F`（`catalog_meta.py` 全量注入）**2/2 通过**：模型写出 `from catalog_meta import VERSION; f"{VERSION}:{item}"`——**直接使用了注入文件里的常量值**。
- `vam_coder_v1.3_V13B`（no-body→**NONE**）**0/2**：模型凭空拼出 `f"cat:{item}:v2"` → 断言失败。
- `vam_coder_v1.2_E`（仅 Digest `--- INDEX ---`，无值）**0/2**，同因。
- `memory_off`（全仓含该文件）1/2、`symbol_full_read`（该文件无符号、未注入）2/2 → 内容改变的是**解法路径的概率**，非严格必要条件，但 V13B−F 的全部 ESR 差（2 episodes = 8.3pp）**恰好就是 I02**。

**对 V13B 的判定修正（诚实反转）**：round2 "no-body→NONE 安全（2/2 通过）"的结论**是 1.5B 特定的**；换模型后同规则立刻失血。且该文件只有 ~95 字节（≈24 tok）——**用 24 token 的节省换一个任务型风险，在任何模型上都是亏本交易**。`has_implementation_body` 对"纯常量文件"是错误信号：常量文件的价值恰恰在**值**而不在体。数据支持的修法：no-body 相关文件回到 FULL（即 V13B 该条规则应撤回，向 `vam_coder_v1.2_F` 收敛）——**是否立 V13C 待预注册，本轮不改代码**。

### 4.2 protocol_violation = reasoning 撞 max_tokens 上限（5 步）

5 例全部是 **completion=1024（触顶）且 response 为空**（如 `v13_D02_vam_coder_v1.2_F_R2` step1、`v13_I01_vam_coder_v1.2_E_R1` step1）：reasoning 模型把 1024 预算全部用于思维链，可见输出为空。按 rev3 §4.5 **如实计入 protocol 失败**（不剔除）；但必须披露其性质：**max_tokens=1024 是为本地非推理模型冻结的配置，与推理模型不兼容**——这是配置-模型交互伪影，波及 E×2、F×1、memory_off×1、symbol_full_read×1、V13B×0。下一轮（若继续）需预注册提高 max_tokens（如 4096）并作敏感性分析。

### 4.3 其余失败仍为能力型

除上述两类：I01 在 V13B/E 全挂（全量系数表在场依旧 noop/实现错，round1 同型）、其余 wrong_implementation 散布；noop 仅 4 步（1.5B 时代的 85 步 noop 大幅消失——强模型确实会"动手改"）。

### 4.4 跨轮对照

| | round1/2（Qwen2.5-Coder-1.5B Q6_K） | round3（deepseek-v4.1-flash-1017） |
| --- | --- | --- |
| ESR 区间 | 0–8.3%，抖动主导 | **83.3–91.7%** |
| 失败主因 | model_noop 85+49 步 | wrong_impl 为主，noop 仅 4 |
| 协议错误 | 0 | 5（reasoning 触顶，§4.2） |
| 注入内容因果性 | 无（给了也不用） | **I02 出现首个因果翻转（§4.1）** |

## 5. 结论

1. **模型能力瓶颈实锤**：架构信号只有在模型越过能力地板后才开始显影（I02 的内容因果翻转是第一个）。
2. **`vam_coder_v1.3_V13B` 的 no-body→NONE 规则被本模型证伪**（I02 0/2 vs `vam_coder_v1.2_F` 2/2；省 24 tok/步）；其头部等长化与"注入 ⊆ F"结构仍然有效，prompt 侧与 F 打平。
3. **VAM 家族对非 VAM 的 token 优势在强模型上保持显著**（−121~−134 prompt/ep，CI 全负），ESR 点估计暂落后 8.3pp（未显著）。
4. 下一轮预注册候选：① 撤回 no-body→NONE（V13C 或回 F）；② max_tokens 提升 + 敏感性分析；③ 多采样稳定 ESR；④ 任务集扩容解开 I01/I02 单点主导。

## 6. 交付物

本目录：`raw_results.csv`（240 步，architecture 全名）、`episode_logs/`（120）、`metrics_summary.csv`、`bootstrap_results.csv`、`failure_analysis.csv`（14 失败集）、`figures/fig1–fig5`、`run_meta.json`（含 p1_common 新哈希与模型换用说明）、`randomization_manifest.json`（seed=20261105）、`analysis_manifest.json`。
追溯：`episode_id = task_id_{architecture}_R{rep}`。密钥仅经环境变量注入，未写入任何产物。
