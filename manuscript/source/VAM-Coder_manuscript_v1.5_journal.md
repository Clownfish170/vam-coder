# VAM-Coder: A Verifiable Context-Management Strategy for Multi-Turn Coding Agents

**Manuscript v1.5 (journal style)** · SCI Q4 · Evidence frozen · Software: MIT  
**Affiliation:** Qingdao University of Technology (undergraduate student)  
**Email:** Xu1764602693@hotmail.com  
**Funding:** This research received no external funding.  
**COI:** none declared

---

# Abstract

Multi-turn coding agents must resend growing repository files and interaction histories at every step, which inflates prompt cost and increases the risk that previously observed file states are absent from the model request actually sent. Truncation, summarization, retrieval, and full-context injection trade context volume against task performance, but reducing volume alone does not ensure that omitted file content remains visible and version-consistent at request issuance.

This paper presents **VAM-Coder**, a verifiable context-management strategy for multi-turn repository-level coding. VAM-Coder couples selective context delivery with two complementary operations. **Visibility Proof (VP)** checks, at the final request boundary, that files whose omission is relied upon remain fully visible with content hashes matching the current workspace; failed checks trigger full-file reinjection and re-verification, and persistent failure blocks the model call. **Verified History Projection (S1)** reduces redundant historical file content by retaining the first and last complete assistant `FILE` blocks for each normalized path and replacing intermediate blocks with non-matching markers. Under a path-keyed, last-write-wins extractor, this projection preserves the extracted visible-file mapping.

In a preregistered main confirmatory study (56 tasks; seven arms × three repetitions = 1,176 episodes per model) on DeepSeek and Qwen, adding S1 to the selective-delivery baseline (**PROJ** = baseline + S1) reduced mean prompt tokens by **18.1%** (Δ = −678.7) and **18.3%** (Δ = −685.0), respectively, while satisfying a prespecified **−12 percentage-point** episode-success non-inferiority margin. The DeepSeek success-rate point estimate decreased by **5.4 pp** (95% CI [−10.1, −1.2]); this drop is reported explicitly rather than treated as unchanged capability. Controlled VP fault injection produced the expected decision in all **30** Phase-2 executions with **zero** unsafe shipments in the tested scenarios. On a separate 10-instance SWE-bench Lite transfer subset, PROJ used approximately **95%** fewer prompt tokens than full-repository injection, which achieved higher observed success rates—an efficiency–capability trade-off, not dominance. The findings do not establish universal task superiority, unrestricted safety, or improvements in inference latency or server-side KV-cache usage.

**Keywords:** coding agents; context management; selective context delivery; visibility proof; history projection; prompt efficiency; non-inferiority; fault injection

---

# 1. Introduction

Multi-turn coding agents interact with software repositories through repeated cycles of inspection, modification, execution, and feedback. At each step the model request concatenates task instructions, selected repository files, tool observations, and conversation history. As the trajectory grows, the request can contain repeated file rewrites, outdated versions, and intermediate observations that are no longer necessary—raising prompt-token cost and pressure on the context window.

Truncation, summarization, retrieval, and memory-oriented policies reduce context volume under different retention trade-offs. Reducing volume, however, introduces a systems-level concern: the relation between information the agent once observed and information actually present in the request submitted to the model. A file may be omitted because it was “sent earlier,” yet its body may later be dropped by truncation, projection, or request reconstruction. A record of past delivery does not establish that complete, current content remains in the final request. Historical delivery, content integrity, and request-level visibility are therefore not equivalent properties.

This distinction matters most in repository-level coding, where full-file rewrites dominate history cost and where an incorrect file version can change edit outcomes. We ask:

> How can multi-turn coding agents reduce redundant context transmission while verifying that selectively omitted workspace content remains visible and version-consistent in the final model input?

**VAM-Coder** answers with two coupled operations rather than a new compressor alone. **Verified History Projection (S1)** removes intermediate complete assistant file blocks while retaining a defined path-level endpoint structure. **Visibility Proof (VP)** then checks the concrete serialized message list immediately before each model call: every in-scope omission must appear complete, with a content hash matching the workspace; otherwise the system reinjects full files and re-verifies, or fails closed. S1 is safe *relative to* the extractor VP uses; VP does not claim to discover all task-relevant files.

We evaluate VAM-Coder in four complementary ways: (i) an initial single-model validation of selective delivery against full-injection references; (ii) a controlled fault-injection study of VP; (iii) a preregistered two-model main confirmatory comparison of projection against the selective-delivery baseline and against truncation, summarization, and retrieval reimplementations; and (iv) a bounded transfer subset on SWE-bench Lite contrasting selective delivery with full-repository injection. Token reduction is never treated as sufficient evidence of improvement: episode success rate (ESR) is assessed under a prespecified non-inferiority margin, and negative and boundary findings are retained.

**Contributions.** (1) A verifiable context-management strategy coupling selective delivery, history projection, and final-request checking. (2) A request-boundary verification mechanism with hash-based version matching, reinjection, and fail-closed behavior. (3) A verifier-compatible history projection with a constructive preservation property under stated extractor rules. (4) A multi-level empirical evaluation spanning two-model confirmatory experiments, policy baselines, ablation, controlled injection, and a bounded external transfer subset—without claiming universal superiority over complete coding-agent systems.

Section 2 positions the work. Section 3 presents the strategy. Section 4 describes the experimental design. Sections 5–7 report baseline validation, main confirmatory results, and transfer results. Sections 8–9 discuss findings, limitations, and conclusions.

---

# 2. Related Work

### 2.1 Context compression and selection

Token-level and extractive compressors (e.g., LLMLingua, Selective Context) reduce input length for general LM workloads [14, 15]. Agent-oriented work stresses granularity and retained structure: AGORA keeps observation–action units [17]; ACON studies compression guidelines for long-horizon agents [26]; FOCUS targets decision-oriented selection of interactions [30]. These methods ask *what to keep*. VAM-Coder asks a complementary systems question: when a file is omitted because its content is assumed available from earlier interaction, does the final request still contain the complete, current file body?

### 2.2 Memory and long-horizon agent context

MemGPT, Generative Agents, Reflexion, and Voyager organize persistent state or skills [6–9]; surveys and benchmarks map agent-memory design [10–13]. S1 addresses one narrow case—repeated complete file blocks in assistant history—by retaining first and last complete blocks per normalized path. It is not general semantic summarization; its preservation claim concerns the path-keyed file map consumed by the implemented verifier, not full conversational equivalence.

### 2.3 Context management in coding agents

SWE-bench provides repository-level issue-resolution settings [18]; SWE-agent, AutoCodeRover, and OpenHands define agent interfaces [19–21]; ContextBench studies context retrieval in coding agents [22]. This paper does not replace those frameworks and does not claim superiority over complete external agents. Comparisons concern context policies inside a shared experimental runner: selective delivery, full-repository injection, truncation, summarization, and retrieval.

### 2.4 Prompt caching and request-level visibility

PagedAttention targets serving memory [25]; vCache and prompt-cache auditing examine cache correctness [23, 24]; recent benchmarks measure compaction cost for long-horizon coding agents [27–31]. VP checks a different property: the content of the concrete message list immediately before the request. A file may have been sent or cached while absent from the next body; a cache record alone does not establish request-level visibility. This paper does not measure cache-hit rates, server-side KV-cache memory, prefill latency, or serving cost.

### 2.5 Positioning

Compression and truncation reduce or replace input; retrieval selects history; memory systems store state; serving systems manage reuse. VAM-Coder couples deterministic projection of repeated assistant file blocks with a request-boundary gate for files whose omission is relied upon. Novelty is the **coupling**, the **final-messages check**, and the **preregistered closed-loop evaluation**—not a claim to be the first compressor or the first history filter.

---

# 3. VAM-Coder Strategy

### 3.1 Problem formulation

Consider an episode with steps \(t=1,\ldots,T\).

- Workspace \(W_t\): normalized relative path \(p\) → body and content hash.
- History \(H_t\): messages available before step \(t\).
- Final messages \(\mathcal{M}_t\): the exact list submitted to the model API.
- Omitted set \(\mathcal{O}_t\): paths whose omission the assembler relies upon this step.
- Edit targets \(E_t\) and candidate-full \(C_t\): must appear in the current user-context block when checks apply.
- Visible-file extractor \(V(\mathcal{M})\): scans complete assistant `FILE` fenced blocks and current-context file blocks; paths are normalized; later occurrences overwrite earlier ones (last-write-wins).

A *complete* assistant `FILE` block has a path line and a closed fence; truncated fragments do not count. Hashes are computed over the normalized extracted body and compared with the workspace. Primary cost metric: mean prompt tokens per episode. Primary capability metric: ESR under a frozen step evaluator.

### 3.2 Processing order

1. Select and trim history inputs.  
2. Optionally apply **S1** to assistant `FILE` blocks.  
3. Build candidate visibility proofs from the projected history with the same extractor.  
4. Assemble the request (must-include files, \(E_t\), \(C_t\), policy-selected context).  
5. Run **VP** on the concrete final message list.  
6. On failure, rebuild with full re-injection of failing paths and re-verify.  
7. Persistent failure → insufficient state; **no model call**.  
8. On success, call the model and apply returned `FILE` blocks to the workspace.

S1 therefore runs before proof construction and assembly; VP runs after assembly at the final-message boundary.

### 3.3 Visibility Proof (VP)

For every \(p\in\mathcal{O}_t\):

\[
p\in V(\mathcal{M}_t)\quad\text{and}\quad \operatorname{SHA256}(V(\mathcal{M}_t)[p])=h_{W_t}(p).
\]

For every \(p\in E_t\cup C_t\), VP additionally requires a complete file block in the **current** user-context message with matching disk hash; history-only visibility is insufficient.

On failure the assembler forces full delivery of failing paths and reconstructs the request; a second failure yields INSUFFICIENT and skips the call.

**Scope.** The checked set follows the system’s own omission, edit-target, and candidate-full bookkeeping. VP does **not** prove that this bookkeeping identified every task-required file; it does not establish semantic completeness of non-file text; it does not eliminate time-of-check/time-of-use races (no cross-process lock through HTTP send). Controlled injection results are not estimates of natural production fault rates.

### 3.4 Verified History Projection (S1)

Editing steps often emit complete replacement bodies for the same path. Because \(V\) is path-keyed with last-write-wins, intermediate complete blocks for a path are redundant *for the extractor*, though not necessarily for every future semantic need.

S1 processes only `role=assistant` messages with complete `FILE` blocks. In the confirmatory *first_last* setting it keeps the **first** and **last** complete block per normalized path and replaces intermediate complete blocks with a short fold marker that contains neither `FILE:` nor a matching fence. Non-assistant messages and unmatched content are unchanged. S1 is deterministic and invokes no additional language model.

### 3.5 Projection-preservation proposition

Let \(V\) be the extractor of §3.1 and \(P\) a projection that retains each path’s last complete assistant `FILE` block and replaces only earlier complete blocks with non-matching markers. Then

\[
V(P(H))=V(H).
\]

*Proof sketch.* For each path, \(V\) depends only on the body of the last complete matching block in scan order. \(P\) preserves that block and removes only strictly earlier complete blocks for the same path, which \(V\) would have overwritten anyway. Fold markers are outside the block grammar. ∎

This is a constructive argument **relative to the implemented extractor and retention rule**, not a theorem over arbitrary parsers or full semantic equivalence. Offline replay on 504 episodes / 2,808 steps found zero mismatches in the extracted file map and pre-send fields under last-only projection; confirmatory runs used *first_last*, which still retains the last block and therefore satisfies the same condition. Finite replay is not formal verification for all inputs; discarded intermediate bodies are gone from the transcript even when the latest body remains.

### 3.6 Auxiliary obligation ledger (S2) and cost

An optional rule-based open-obligation reminder (S2) may render compact lines between task and context. S2 is an **auxiliary heuristic**, not a core contribution or a verified semantic completion detector; syntactic or file-change cues can close obligations without establishing semantic completion. Because the confirmatory design has no baseline+S2-only arm, the independent effect of S2 cannot be identified from the combined configuration.

S1 scans assistant strings and maintains a path dictionary; VP scans final messages and hashes checked bodies. Both costs are linear in scanned text plus hashing. Experiments report prompt tokens only—not end-to-end latency, prefill time, or KV-cache memory.

---

# 4. Experimental Setup

### 4.1 Research questions

- **RQ1 (efficiency).** How does selective delivery with projection compare with alternative context policies in prompt tokens?  
- **RQ2 (capability).** Does the projected configuration meet the prespecified −12 pp ESR non-inferiority margin relative to the selective-delivery baseline?  
- **RQ3 (delivery reliability).** Under controlled visibility, version, history, and budget faults, does VP make the expected decisions and recovery or fail-closed responses?  
- **RQ4 (mechanism and robustness).** What incremental effect is associated with S1, and how robust are primary directions across two model families and post-hoc archetype-cluster resampling?

### 4.2 Models, tasks, and arms

Confirmatory evaluation used `deepseek-v4.1-flash-1017` and `qwen3-coder-flash` through the same OpenAI-compatible MaaS endpoint (temperature 0, seed 0, max generation 2,048 tokens). The task set contained **56** multi-step repository-editing tasks: 48 independent tasks (24 archetypes × two variants) plus eight dose tasks treated as singleton clusters.

Each model used seven arms × three repetitions per task–arm cell (168 episodes per arm; 1,176 episodes per model). The statistical unit for paired comparisons was the **task**; arm values were means over the three repetitions.

**Arm definitions (used in tables and figures):**

| Short name | Configuration |
|---|---|
| **F** | Selective-delivery baseline: full history retention; no S1/S2 |
| **PROJ** | F + S1 only (projection) |
| **SAH** | F + S1 + auxiliary S2 ledger (combined configuration) |
| TRUNC | Sliding-window history (1,300 characters/step) |
| SUMM | Same-model summarization; summarizer prompt tokens included in prompt accounting |
| RETR | BM25 top-3 history retrieval; latest history retained |
| MOFF | Full-repository injection each step (context policy, not an external agent) |

TRUNC, SUMM, and RETR are **local reimplementations**, not original-author code. Their settings follow the main-study prompt accounting (including summarizer prompt tokens for SUMM) and are fixed before the confirmatory comparisons; they are intended as same-runner policy references rather than official replications of the original systems. **PROJ−F** estimates the incremental effect of S1. **SAH−F** estimates F+S1+S2 jointly and **must not** be read as an isolated S2 effect.

### 4.3 Metrics and statistics

Primary efficiency metric: mean prompt tokens per episode. Primary capability metric: ESR (frozen step evaluator). Non-inferiority margin: **−12 pp** on ESR (lower 95% CI bound ≥ −12 pp).

For each model, paired differences used 56 tasks after averaging repetitions within task×arm. CIs: task-level bootstrap, seed 20261102, 10,000 replicates. Two-sided sign-flip tests with Holm correction within prespecified families. Episode counts describe execution volume, not the independent sample size.

Post-hoc archetype-cluster bootstrap (5,000 replicates) and leave-one-archetype-out analysis are **sensitivity** checks, not preregistered confirmatory tests. Clusters: 32 (24 archetypes × two tasks + eight dose singletons).

### 4.4 Controlled VP fault injection

**Phase 1:** 31 deterministic scenarios—13 unsafe/omission negatives, nine ordinary positives, eight false-block controls, and one boundary case (C4; safe-omission denominator 10). VP is compared with a content-hash baseline (B1) and an ever-sent cache baseline (B2).

**Phase 2:** 10 frozen scenarios × three repetitions (30 executions) embedded in the real runner via test-side monkeypatching (production code unchanged), DeepSeek. Evaluated as per-scenario assertions, not as statistical generalization.

---

# 5. Baseline Validation of Selective Delivery

This section reports an earlier single-model confirmation of the selective-delivery baseline that preceded the main two-model study. It uses its own task suite and protocol; **no episodes, task-level estimates, or CIs are pooled** with the main confirmatory analysis. It does not isolate the later final-message verifier.

### 5.1 Protocol

Model: `deepseek-v4.1-flash-1017` (temperature 0, seed 0, 2,048-token limit). Tasks: 48 repository-editing items from eight parameterized families (16 short / 16 medium / 16 long; 272 steps total). Three architectures × five repetitions = 240 episodes each (720 total); 4,080 step rows. Architectures: selective-delivery baseline (**F**), `memory_off` (full injection reference), and `symbol_full_read`. Metrics and bootstrap follow the same task-level rules as §4.3 (margin −12 pp; Holm on two primary prompt comparisons).

### 5.2 Results

Mean prompt tokens/episode: **2,510.2** (F) vs **3,287.2** (`memory_off`) and **3,311.4** (`symbol_full_read`). ESR: **92.92%** (223/240), **93.75%** (225/240), **93.75%** (225/240). F reduced prompt tokens by **23.6%** and **24.2%** versus the two references, with observed ESR 0.83 pp lower than either.

Paired F − reference differences: prompt **−777.0** (95% CI [−974.8, −584.4]) and **−801.2** ([−1,003.3, −603.3]); TPAE −786.6 and −845.3 with corresponding CIs; both prompt sign-flip tests Holm-adjusted \(p=0.0002\). All eight task-family mean prompt differences were negative (family sign-flip \(p=0.0079\), \(0.0072\)). ESR differences: **−0.83 pp** vs `memory_off` (CI [−4.17, +2.92]) and vs `symbol_full_read` (CI [−5.42, +2.92]); both lower bounds above −12 pp → non-inferiority met. Intervals include zero: **no superiority claim**.

**Table 1.** Architecture-level results of the baseline validation study. TPAE = total prompt+completion tokens/episode; TPSE = tokens per successful episode. SDs describe episode-level prompt variation, not uncertainty in the paired task-level effect.

| Architecture | Episodes | Success / total | ESR | Prompt / episode (SD) | TPAE | TPSE |
|---|---|---|---|---|---|---|
| F (selective delivery) | 240 | 223 / 240 | 92.92% | 2,510.2 (1,910.5) | 3,339.8 | 3,594.4 |
| memory_off | 240 | 225 / 240 | 93.75% | 3,287.2 (2,605.7) | 4,126.4 | 4,401.5 |
| symbol_full_read | 240 | 225 / 240 | 93.75% | 3,311.4 (2,621.0) | 4,185.1 | 4,464.1 |

**Table 2.** Preregistered paired contrasts (F − reference). CIs are task-cluster bootstrap intervals; ESR margin −12 pp.

| Contrast | Δ prompt (95% CI) | Δ TPAE (95% CI) | Δ ESR (95% CI) | Non-inferiority |
|---|---|---|---|---|
| F − memory_off | −777.0 [−974.8, −584.4] | −786.6 [−979.3, −601.8] | −0.83 pp [−4.17, +2.92] | PASS |
| F − symbol_full_read | −801.2 [−1,003.3, −603.3] | −845.3 [−1,058.7, −640.1] | −0.83 pp [−5.42, +2.92] | PASS |

Prompt savings increased with task length (long-task difference ≈1,733.9 tokens/episode, ≈25.3%). There were 47 failed episodes across three architectures; one short-task variant failed in all 15 repetitions on all arms and remained in the ESR denominator per preregistration. Protocol violations (2 / 6 / 4) counted as failures. F had zero INSUFFICIENT steps and zero delivery-hazard events under this accounting. Scope limits: eight shared families, one hosted endpoint, retained protocol violations—**not** independent evidence for every later VP component, cross-provider replication, or latency/KV improvements.

---

# 6. Main Confirmatory Evaluation

### 6.1 Baseline and ablation context

Within the main study, **F** is the selective-delivery baseline against which PROJ and SAH are compared. The baseline validation in Section 5 is separate and not pooled.

In a **mechanism ablation** batch (1,680 episodes), disabling the omission/reuse delivery path (historical name: the O′ / no-VP path—not an isolated final-gate-only switch) increased prompt cost by **397.6** tokens/episode relative to F (ablation − F; 95% CI [275.4, 524.8]). ESR difference: **+0.42 pp** (ablation − F; CI [−2.08, +2.92]), crossing zero—**no detectable** ESR difference under this ablation, not proof of identical ESR. This isolates the cost of the omission/reuse path in that configuration; it does **not** isolate the final-message verifier alone and is **not** an S1 ablation. History redaction also cut tokens but hurt visible-context recall; must-closure ablation had a small prompt effect (~+24 tokens).

**Figure 1** (prompt) and **Figure 2** (ESR) report F, PROJ, and SAH; **Figure 3** compares six context-management methods; **Figure 4** is the efficiency–capability plane; **Figure 5** shows the mechanism ablation; **Figure 6a/6b** show forest plots for prompt and ESR.

### 6.2 Controlled fault-injection results

**Phase 1:** all 31 scenarios received expected decisions. Unsafe-omission rate **0/13**; safe-omission **10/10** (nine positives + boundary C4); false-block **0**; fallback success **13/13**. On visibility scenarios V1–V5, detection rates were VP **1.00**, content-hash **0.00**, ever-sent cache **0.80**. VP’s exclusive detection was V4: content hash valid and file previously sent, but the block **absent from final messages**.

**Phase 2:** expected decision in **30/30** executions (10 scenarios × 3); **unsafe_ship = 0**; delivery-omission-hazard events **0**. An initial 18 executions were superseded after a task-mapping issue made some injected omissions unreachable; the final 30 use corrected mappings; superseded records are archived and excluded. Results support VP behavior **under tested controlled injections only**—not production fault rates or universal safety.

### 6.3 Main comparison: projection versus baseline

Each arm: 168 episodes/model; paired analysis on 56 tasks.

**S1 efficiency (PROJ−F).** DeepSeek: **−678.7** prompt tokens (95% CI [−960.7, −431.2]), **−18.1%**. Qwen: **−685.0** ([−949.4, −442.3]), **−18.3%**. Both CIs strictly below zero.

**S1 capability (PROJ−F ESR).** DeepSeek **−5.4 pp** ([−10.1, −1.2]); Qwen **+2.4 pp** ([−0.6, +6.0]). Both lower bounds exceed −12 pp → non-inferiority met. DeepSeek nevertheless shows a measurable decrease with less margin headroom; we interpret **non-inferiority under the margin**, not unchanged or improved capability.

**Combined configuration (SAH−F).** Prompt **−632.6** (16.9%) DeepSeek and **−697.3** (18.6%) Qwen; ESR **−1.2 pp** and **+1.8 pp** with CIs [−5.4, +3.0] and [−0.6, +5.4]. These describe F+S1+S2 jointly; without a baseline+S2-only arm they do **not** identify an independent S2 effect.

**Table 3.** Main confirmatory arm means (168 episodes/arm/model).

| Model | Arm | ESR | Prompt / episode |
|---|---|---|---|
| DeepSeek | F | 0.649 | 3747.5 |
| DeepSeek | PROJ (F+S1) | 0.595 | 3068.9 |
| DeepSeek | SAH (F+S1+S2) | 0.637 | 3114.9 |
| Qwen | F | 0.512 | 3740.2 |
| Qwen | PROJ (F+S1) | 0.536 | 3055.2 |
| Qwen | SAH (F+S1+S2) | 0.530 | 3042.9 |

### 6.4 External context-policy baselines

TRUNC had the lowest mean prompt (2,456.4 DeepSeek; 2,347.2 Qwen) by discarding older history **without** VP’s delivery check. SAH was non-inferior to TRUNC on ESR (+0.6 pp, CI [−1.8, +3.0]; 0.0 pp, [−3.6, +3.6]) but not cheaper in prompt. SAH used **1,891.6** fewer prompt tokens than SUMM on DeepSeek and **1,205.9** on Qwen. Descriptive SAH−RETR prompt differences (−153.6, −133.0) are not Holm-gated primary claims. SUMM is most expensive once summarizer prompts are counted (5,006.5 / 4,248.7). The proposed configuration does **not** dominate all alternatives on every metric.

**Table 4.** Six context-management methods (same main batch; external arms are local reimplementations).

| Method | DeepSeek prompt | DeepSeek ESR | Qwen prompt | Qwen ESR |
|---|---|---|---|---|
| F | 3747.5 | 0.649 | 3740.2 | 0.512 |
| PROJ | 3068.9 | 0.595 | 3055.2 | 0.536 |
| SAH | 3114.9 | 0.637 | 3042.9 | 0.530 |
| TRUNC | 2456.4 | 0.631 | 2347.2 | 0.530 |
| SUMM | 5006.5 | 0.637 | 4248.7 | 0.506 |
| RETR | 3268.5 | 0.643 | 3175.9 | 0.488 |

### 6.5 Cross-model consistency

Primary PROJ−F prompt directions match on both models; both meet ESR non-inferiority. Absolute ESR levels differ (F: 0.649 vs 0.512), so models are reported separately, not pooled. This is directional consistency across two families on **one** MaaS endpoint—not multi-provider replication.

### 6.6 Archetype-cluster sensitivity (post-hoc)

Resampling 32 clusters (B=5,000): all four primary prompt CIs remain strictly below zero (e.g., DeepSeek PROJ−F cluster CI [−1,050.9, −340.5]; SAH−F [−977.1, −317.1]). All ESR non-inferiority lower bounds stay ≥ −12 pp (tightest ≈ −9.6 pp, DeepSeek PROJ−F). Leave-one-cluster-out does not flip prompt signs or break non-inferiority. Cluster prompt intervals are ≈1.34–1.39× wider than task-level intervals—task resampling understates uncertainty when tasks share archetypes. This analysis is sensitivity only.

### 6.7 Supporting and negative evidence

Offline replay on a historical deep run (504 episodes, 2,808 steps) with last-only projection found **zero** mismatches in the file map and pre-send fields (see §3.5 regarding first_last vs last-only). A dedicated dual-token experiment did **not** establish an independent contribution under its frozen decision rules and is **not** evidence for the present method. Other exploratory branches are excluded from confirmatory claims.

---

# 7. Transfer Evaluation on a SWE-bench Lite Subset

### 7.1 Scope and protocol

A separate transfer evaluation used a **10-instance** subset of the SWE-bench Lite **test** split: `requests-3362`, `requests-863`, `requests-1963`, `pytest-7432`, `pytest-11143`, `pytest-5413`, `pytest-6116`, `flask-4045`, `flask-5063`, `pylint-7993`. Execution used local Docker and FAIL_TO_PASS tests; this is **not** the official full SWE-bench leaderboard protocol. Selection favored bounded patches and lighter environments (≤3 instances/repository; 1–12 FAIL_TO_PASS tests/instance).

Arms: **F**; **PROJ** (F+S1, first_last); **MOFF** (full-repository injection each step—**not** an external coding agent). Per model: 10 instances × 3 arms × 3 repetitions = 90 episodes (180 total). Statistical unit: **instance** (\(n=10\)); repetitions averaged before paired bootstrap.

DeepSeek: `deepseek-v4.1-flash-1017`. Transfer Qwen: `qwen3.8-flash` (differs from confirmatory `qwen3-coder-flash` because the original endpoint was unavailable). Temperature 0, seed 0, max_tokens 16,384; budget 16,384; window 65,536. Qwen timeouts were raised from 600s to 1,200s with thinking disabled after initial timeouts; the final run had no timeouts. Some DeepSeek completions used a token-plan endpoint with the same model ID. `flask-5063` F and PROJ episodes hit `REQUIRED_CONTEXT_EXCEEDS_LIMIT` and remained ESR failures under the frozen no-retry rule.

### 7.2 Prompt efficiency and success

DeepSeek: F ESR 80.0% (24/30) ≈24.1k prompt; PROJ 83.3% (25/30) ≈24.1k; MOFF 93.3% (28/30) ≈474k. Qwen: F 86.7% (26/30) ≈24.1k; PROJ 86.7% (26/30) ≈24.1k; MOFF 100% (30/30) ≈518k.

Versus MOFF, PROJ reduced observed prompt volume by ≈**95.0%** (DeepSeek) and **95.3%** (Qwen). Paired PROJ−MOFF prompt: ≈−452k (CI [−593k, −311k]) and −496k ([−642k, −345k]). **MOFF had higher observed ESR** (PROJ−MOFF: −10 pp, CI [−33, +7]; −13 pp, [−33, 0]). Wide intervals and \(n=10\) preclude strong capability conclusions.

PROJ did **not** show incremental prompt reduction over F in this single-step setting (≈0 DeepSeek; +1 token Qwen; CIs span zero)—consistent with little multi-turn history for S1 to fold. The transfer result supports selective delivery vs full-repository injection as an **efficiency–capability trade-off**, not S1 benefit in this format, and not dominance of VAM-Coder.

### 7.3 Interpretation and limits

The subset is small, single-step, and model-substituted for Qwen; it does not recreate long multi-turn histories where S1 matters most. **This small transfer subset serves only as a preliminary external transfer check rather than a comprehensive benchmark evaluation.** It does not compare complete systems such as SWE-agent or OpenHands. The API `cached_tokens` field was recorded but is **not** a measurement of server-side KV-cache memory; no claims about KV capacity, prefill latency, end-to-end latency, or serving cost are drawn. Transfer results are **not pooled** with the 56-task main study.

---

# 8. Discussion and Threats to Validity

### 8.1 What the results establish

Under the frozen protocol, path-based projection reduces prompt transmission while preserving the file map used by a final-message verifier, relative to a specified parser and retention rule. In the main study, PROJ cut prompt tokens by ≈18% versus F on both models under a −12 pp non-inferiority margin, with an explicit DeepSeek ESR decrease of 5.4 pp. VP’s value relative to naive hash/ever-sent checks appears on the V4 class of faults (unchanged content, previously sent, absent from final messages). S1’s preservation property is consistent with shared-extractor design and large offline replay—not formal verification of arbitrary message languages.

### 8.2 Relation to other context-management methods

TRUNC remains the cheapest same-batch method on prompt tokens; VP+S1 is not a token-minimum optimum. Its objective differs: cut repeated file bodies while checking delivery of in-scope omissions. SUMM includes summarizer overhead in this accounting; RETR trades full history for selected messages. External arms are reimplementations. The approach is complementary to asynchronous compaction and prefix-cache work; because no latency, prefill, or KV measurements were collected, serving-level efficiency is out of scope.

### 8.3 Limitations

1. Controlled **micro-repository** tasks, not industrial monorepos or full SWE-bench.  
2. Two model families on **one** endpoint—directional consistency, not multi-provider replication; temperature 0 is not bit-deterministic on hosted APIs (task is the statistical unit).  
3. Shared archetypes; post-hoc cluster analysis widens prompt CIs (~34–39%) without reversing primary directions.  
4. S1 preservation is relative to a regex extractor, path normalization, complete-block grammar, and last-write-wins map—not full semantic equivalence; replay used last-only while confirmatory used first_last (shared last-block condition).  
5. VP scope depends on prior identification of omissions/edit targets; no proof of complete discovery; a time-of-check/time-of-use window remains because the implementation does not hold a lock across verification and HTTP send. Production hardening (retry, monitoring of failed checks, stronger request serialization) is outside the scope of this paper.  
6. Phase-1/2 fault injection is controlled; zero unsafe ships apply only to frozen scenarios; phase-2 evidence is from one model family.  
7. S2 is a rule-based auxiliary heuristic without a baseline+S2-only arm; no independent S2 claim.  
8. External baselines are local reimplementations with possible parameterization differences.

### 8.4 Practical implications

If a system omits files because they were believed delivered earlier, a final-message verifier makes that assumption explicit and testable. If the transcript is dominated by repeated complete-file rewrites, path-based projection can remove intermediate bodies while preserving the map that verifier consumes. Deploy with explicit check scopes, robust serialization, and monitoring of check-to-send races.

---

# 9. Conclusion

We presented **VAM-Coder**, a verifiable context-management strategy for multi-turn coding agents, combining selective context delivery with **S1** (history projection) and **VP** (final-request visibility and version checks, with reinjection and fail-closed behavior). In the main two-model confirmatory study, PROJ reduced prompt tokens by **18.1%** and **18.3%** versus the selective-delivery baseline while meeting the **−12 pp** ESR non-inferiority margin; the DeepSeek ESR point estimate decreased by **5.4 pp** and is reported as such. A separate 10-instance SWE-bench Lite subset showed ≈**95%** lower prompt volume than full-repository injection, with higher observed success for full injection—an efficiency–capability trade-off. Controlled VP fault injection met expected decisions in the tested scenarios. Together, the evidence supports VAM-Coder as a context-management strategy that reduces redundant transmission while making selected omission assumptions explicit and testable. The findings do **not** establish universal task superiority, semantic equivalence of arbitrary histories, unrestricted safety, or improvements in latency, prefill time, or server-side KV-cache behavior.

---

# Data and Code Availability

The VAM-Coder software is released under the MIT License. Implementation, frozen preregistration documents, experiment runners, and analysis scripts are available in the VAM-Coder repository (README and reproducibility documentation). Confirmatory batches, fault-injection scenarios, and transfer protocols are retained with run metadata and code snapshots under the experiment directories. Exact commit identifiers and preregistration freeze hashes are listed in the repository release accompanying this submission. Raw model outputs are retained under institutional policy; derived statistics reproduce from published scripts and frozen tables. Corresponding author: Qingdao University of Technology; email Xu1764602693@hotmail.com.

**Funding:** This research received no external funding.  
**Conflicts of Interest:** none declared.  
**Generative AI use:** Drafting and revision assistance used large-language-model tools for language polishing and document formatting only. All experimental design, data, statistical analysis, and scientific claims originate from the authors and the frozen experimental record; no generative AI system produced or altered reported results.

---

# References

[1] Nelson F. Liu et al. Lost in the Middle: How Language Models Use Long Contexts. TACL, 12:157–173, 2024. arXiv:2307.03172.  
[2] Hsieh et al. RULER. COLM, 2024. arXiv:2404.06654.  
[3] Yushi Bai et al. LongBench. ACL, 2024. arXiv:2308.14508.  
[4] Yue Xue. When and How Context Rot Appears in Coding Agents. arXiv:2607.17937, 2026.  
[5] Shijie Xia et al. Diagnosing and Mitigating Context Rot in Long-horizon Search. arXiv:2606.29718, 2026.  
[6] Charles Packer et al. MemGPT. arXiv:2310.08560, 2023.  
[7] Joon Sung Park et al. Generative Agents. UIST, 2023. arXiv:2304.03442.  
[8] Noah Shinn et al. Reflexion. NeurIPS, 2023. arXiv:2303.11366.  
[9] Guanzhi Wang et al. Voyager. arXiv:2305.16291, 2023.  
[10] Zepeng Zhang et al. A Survey on the Memory Mechanism of LLM Based Agents. arXiv:2404.13501, 2024.  
[11] Jinghao Luo et al. From Storage to Experience: A Survey of LLM Agent Memory Mechanisms. ACL Findings, 2026.  
[12] Mingyu Zhang et al. TrawMem. arXiv:2610.36918, 2026.  
[13] Yuyao Wang et al. EvoMemBench. arXiv:2605.18421, 2026.  
[14] Huiqiang Jiang et al. LLMLingua. EMNLP, 2023. arXiv:2310.05736.  
[15] Yuhui Li et al. Selective Context. EMNLP, 2023. arXiv:2310.06201.  
[16] Shamin Chokshi. Lexical Prompt Compression. arXiv:2609.13154, 2026.  
[17] Haoran Zhang and Zhaohua Sun. AGORA. arXiv:2605.26596, 2026.  
[18] Carlos E. Jimenez et al. SWE-bench. ICLR, 2024. arXiv:2310.06770.  
[19] John Yang et al. SWE-agent. NeurIPS, 2024. arXiv:2405.15793.  
[20] X. Zhang et al. AutoCodeRover. ISSTA, 2024. arXiv:2404.05427.  
[21] Shuyan Wang et al. OpenHands. ICLR, 2025. arXiv:2407.16741.  
[22] Han Li et al. ContextBench. arXiv:2602.05892, 2026.  
[23] Luis Gaspar Schroeder et al. vCache. ICLR, 2026. arXiv:2502.03771.  
[24] Chenchen Gu et al. Auditing Prompt Caching in Language Model APIs. ICML, 2025. arXiv:2502.07776.  
[25] Woosuk Kwon et al. PagedAttention. SOSP, 2023. arXiv:2309.06180.  
[26] Minki Kang et al. ACON. ICML, 2026. arXiv:2510.00615.  
[27] Ruopei Sun et al. Compact-Bench. arXiv:2610.31710, 2026.  
[28] Le Chen et al. Measure Before You Manage. arXiv:2608.31057, 2026.  
[29] Ritul Satish et al. Beyond Token Savings. arXiv:2609.32961, 2026.  
[30] Shantanu Dixit et al. FOCUS. arXiv:2609.37590, 2026.  
[31] Banruo Liu et al. CompactionBench. Microsoft Research preprint, 2026.  
[32] Patrick Lewis et al. Retrieval-Augmented Generation. NeurIPS, 2020. arXiv:2005.11401.  
[33] Yunfan Gao et al. RAG: A Survey. arXiv:2312.10997, 2023.

---

## Figure file map (internal; strip before journal PDF if required)

| Figure | File under `figures/` |
|---|---|
| Figure 1 | `fig4_prompt_line.png` |
| Figure 2 | `fig5_esr_line.png` |
| Figure 3 | `fig6_methods_bars.png` |
| Figure 4 | `fig7_tradeoff_scatter.png` |
| Figure 5 | `fig5_p2_ablation.png` |
| Figure 6a | `fig9a_forest_prompt.png` |
| Figure 6b | `fig9b_forest_esr.png` |

*End of manuscript v1.5 (journal-style). Quantitative claims match frozen experimental artifacts; internal study codes are replaced by descriptive names except where short arm labels (F/PROJ/SAH/TRUNC/SUMM/RETR/MOFF) are defined in §4.2.*
