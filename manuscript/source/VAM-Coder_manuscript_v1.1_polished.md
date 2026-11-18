# VAM-Coder: A Verifiable Context-Management Strategy for Multi-Turn Coding Agents

**Manuscript v1.1 (polished from v1.0 restructured)** · SCI Q4 · Evidence frozen
**Author:** Clownfish · Affiliation / Email / Funding: TODO before submission
**Software:** MIT (VAM-Coder) · **Figures:** `../figures/`

---

# VAM-Coder: A Verifiable Context-Management Strategy for Multi-Turn Coding Agents
# Abstract
Multi-turn coding agents repeatedly process repository files and interaction histories, leading to substantial prompt growth and increasing the risk that previously observed file states are no longer available in the model’s actual input. Existing context-management strategies—including truncation, summarization, retrieval, and full-context injection—offer different trade-offs between context volume and task performance. However, reducing context size alone does not ensure that omitted file content remains visible and version-consistent when a model request is issued.

This paper presents VAM-Coder, a verifiable context-management strategy for multi-turn repository-level coding tasks. VAM-Coder combines selective context delivery with two complementary mechanisms. Visibility Proof (VP) verifies, at the final request boundary, that files whose omission is relied upon remain completely visible and consistent with their current workspace versions. Failed checks trigger full-file reinjection and re-verification, while persistent failures prevent the model call. Verified History Projection (S1) reduces redundant historical file content by retaining the first and last complete assistant-generated file blocks for each normalized path and replacing intermediate blocks with non-matching markers. Under the specified path-keyed, last-write-wins extractor, this projection preserves the extracted visible-file mapping.

We evaluate VAM-Coder through multi-model experiments, internal ablations, controlled fault injection, and comparisons with alternative context-management strategies. In a 56-task confirmatory study, adding S1 to the selective-delivery baseline reduced mean prompt tokens by 18.1% and 18.3% on two model families, respectively, while satisfying a prespecified 12-percentage-point episode-success non-inferiority margin. In a separate 10-instance SWE-bench Lite transfer subset, the VAM-Coder PROJ configuration reduced observed prompt-token volume by approximately 95% relative to full-repository injection, although the latter achieved higher observed success rates. Controlled VP fault-injection tests produced the expected decisions in all 30 Phase-2 executions, with no unsafe shipment in the tested scenarios. These findings indicate that VAM-Coder can reduce redundant context transmission while explicitly checking the visibility and version consistency of in-scope files. Its effectiveness is workload-dependent; the results do not establish universal task superiority, unrestricted safety, or improvements in inference latency or server-side KV-cache usage.

**Keywords:** coding agents; context management; selective context delivery; visibility verification; history projection; prompt efficiency; non-inferiority; fault injection; repository-level software engineering
# 1. Introduction
Multi-turn coding agents interact with software repositories through repeated cycles of code inspection, modification, execution, and feedback. At each interaction step, the agent constructs a model request from task instructions, selected repository files, tool observations, and preceding conversation history. As the interaction progresses, the accumulated context can contain repeated representations of the same files, outdated file versions, and intermediate observations that are no longer necessary for subsequent decisions. This growth increases prompt-token consumption and places additional pressure on the model’s finite context window.

A variety of context-management strategies have been proposed to address this problem. Truncation limits the amount of retained history, summarization replaces detailed interactions with condensed representations, retrieval selects potentially relevant historical information, and memory-oriented approaches organize persistent information for later use. These strategies provide different trade-offs between context size, information retention, and task performance. However, reducing the amount of context supplied to a model introduces a further systems-level concern: the relationship between information previously observed by the agent and information actually present in the request submitted to the model.

This distinction is particularly important in repository-level coding tasks. An agent may decide not to include a file in the current request because that file was transmitted during an earlier interaction. Nevertheless, the corresponding file body may subsequently have been removed by history truncation, projection, or request reconstruction. Similarly, a record indicating that a file was previously transmitted does not establish that its complete and current content remains available in the final request. Consequently, historical delivery, content integrity, and request-level visibility should not be treated as equivalent properties.

This paper presents VAM-Coder, a verifiable context-management strategy designed for multi-turn coding agents. Rather than relying exclusively on context reduction or retention heuristics, VAM-Coder combines selective context delivery with explicit verification of the information whose omission is being relied upon. Its design is based on two complementary operations: reducing redundant historical file representations and checking the visibility and version consistency of in-scope files immediately before a model request is issued.

The first operation, Verified History Projection (S1), reduces repeated complete file representations in assistant-generated history. For each normalized file path, the confirmatory configuration retains the first and last complete assistant-generated file blocks and replaces intermediate complete blocks with markers that are not recognized by the file extractor. This design preserves the last complete representation used by the system’s path-keyed, last-write-wins visible-file map. The resulting preservation property is explicitly relative to the implemented extractor; it does not imply that the removed intermediate blocks are semantically irrelevant to every possible future task.

The second operation, Visibility Proof (VP), checks the concrete serialized message list at the final model-request boundary. For each file whose omission is relied upon, VP verifies that a complete file body is visible and that its content hash matches the corresponding current workspace version. Files designated as edit targets or candidate-full files are subject to additional current-context requirements. If verification fails, VAM-Coder reconstructs the request with the relevant files fully injected and repeats the check. If the rebuilt request still fails verification, the system blocks the model call rather than proceeding with an unverified request.

The two operations address different but connected aspects of context management. S1 reduces repeated historical file content while preserving the file mapping consumed by the verifier. VP checks whether the assumptions made during selective delivery hold in the actual request that is about to be transmitted. Together, they establish a context-management workflow in which historical projection is constrained by a defined preservation condition and selective omission is subject to a final delivery check.

We evaluate VAM-Coder through complementary experiments. A preregistered multi-model study involving 56 repository-editing tasks examines prompt-token efficiency, episode success rate, and the incremental effect of S1. Alternative context-management baselines, including truncation, summarization, and retrieval, provide additional reference points. A separate SWE-bench Lite subset experiment compares selective delivery with full-repository context injection under a different task and model configuration. Finally, controlled fault-injection experiments examine whether VP makes the expected verification and recovery decisions under predefined visibility, version, and request-construction conditions.

The evaluation distinguishes context efficiency from task capability rather than treating token reduction as sufficient evidence of improvement. The results show that VAM-Coder can substantially reduce prompt volume in the evaluated settings, but the lowest-context strategy does not necessarily achieve the highest observed task success rate. The study therefore examines the efficiency–capability trade-off and the conditions under which explicit delivery verification can make selective context management more reliable.

The contributions of this paper are fourfold: (1) a verifiable context-management strategy for multi-turn coding agents that combines selective delivery, history projection, and final-request checking; (2) a request-boundary verification mechanism with hash-based version matching, reinjection, and fail-closed behavior; (3) a verifier-compatible history projection method with a constructive preservation property under specified extractor rules; and (4) a multi-level empirical evaluation combining two-model confirmatory experiments, alternative context-policy comparisons, a bounded SWE-bench Lite transfer subset, internal ablations, and controlled fault injection. The paper reports negative and boundary findings and does not claim universal superiority over complete external coding-agent systems.

The remainder of this paper is organized as follows. Section 2 reviews related work. Section 3 presents the VAM-Coder strategy and its constituent mechanisms. Section 4 describes the experimental design. Sections 5–7 report the historical validation, confirmatory evaluation, and transfer evaluation. Section 8 discusses the findings and limitations, and Section 9 concludes the paper.

# 2. Related Work
## 2.1 Context compression and context selection
Prompt-compression methods such as LLMLingua and Selective Context reduce input length through token-level or segment-level selection [14, 15]. Agent-oriented approaches emphasize that compression granularity and retained structure matter. AGORA, for example, retains structured observation–action units rather than relying on unrestricted token-level extraction [17]. ACON studies failure-informed natural-language compression guidelines [26], while FOCUS investigates decision-oriented selection of historical interactions [30]. These methods address which information should be retained and how it should be represented. VAM-Coder addresses a complementary systems question: when a file is omitted because its content is assumed to remain available from an earlier interaction, does the final request actually contain the complete, current file body?

## 2.2 Memory management and long-horizon agent context
Memory systems such as MemGPT, Generative Agents, Reflexion, and Voyager organize persistent state, experiences, reflections, or reusable skills [6–9]. Surveys and recent benchmarks examine the diversity of agent-memory architectures and their evaluation [10–13]. Coding-agent histories are heterogeneous: instructions, tool outputs, source artifacts, and agent-generated state may require different retention policies. S1 addresses one narrow case—repeated complete file blocks in assistant-generated history—by retaining the first and last complete block per normalized path. It does not perform general semantic summarization. Its preservation claim concerns the path-keyed, last-write-wins file map consumed by the implemented verifier, not the full semantic equivalence of the conversation.

## 2.3 Context management in coding agents
Repository-level benchmarks such as SWE-bench provide task settings for evaluating software-engineering agents [18]. Systems such as SWE-agent, AutoCodeRover, and OpenHands provide different interfaces and workflows for repository interaction [19–21], while ContextBench examines context retrieval in coding-agent settings [22]. These works establish the importance of repository context and agent architecture. The present study does not introduce a replacement for these general coding-agent frameworks and does not claim superiority over complete external agents. Its comparisons concern context-management policies evaluated within the experimental runner: selective delivery, full-repository injection, truncation, summarization, and retrieval.

## 2.4 Prompt caching and request-level visibility
PagedAttention concerns memory management for LLM serving [25], while vCache and prompt-cache auditing examine correctness or auditing questions associated with prompt-cache reuse [23, 24]. Recent work benchmarks the cost of context compaction for long-horizon coding agents [27–31]. VP checks a different property: the content of the concrete serialized message list immediately before the request. A file may have been sent previously or recorded in a cache while its body is absent from the next request. A cache record alone therefore does not establish request-level visibility. These directions may be complementary, but this paper does not measure cache-hit rates, server-side KV-cache memory, prefill latency, or serving cost.

## 2.5 Positioning of VAM-Coder
The principal distinction of VAM-Coder is the coupling of selective context management with an explicit final-request check. Prompt compression and truncation reduce or replace input content; retrieval selects historical information; memory systems organize persistent state; serving systems manage computational reuse. VAM-Coder combines a deterministic projection of repeated assistant file blocks with a request-boundary verification gate for files whose omission is relied upon. It is not proposed as a universally optimal compressor or a general semantic memory system. Its contribution is a testable context-management workflow with a defined visibility/version condition and a bounded empirical evaluation.

# 3. VAM-Coder Strategy Design
## 3.1 Problem formulation
Consider a multi-turn episode with steps \(t=1,\ldots,T\). Let:

- \(W_t\) denote the current workspace, mapping each normalized relative path \(p\) to its current file body and content hash;
- \(H_t\) denote the interaction history available before step \(t\);
- \(\mathcal{M}_t\) denote the concrete ordered list of messages submitted to the model API;
- \(\mathcal{O}_t\) denote the set of files whose omission is being relied upon at step \(t\);
- \(E_t\) and \(C_t\) denote edit targets and candidate-full files, respectively, which must be present in the current user-context block when the corresponding checks apply.
The visible-file extractor \(V(\mathcal{M})\) scans complete assistant FILE fenced blocks and current-context FILE blocks. Paths are normalized, and later occurrences overwrite earlier ones. Thus, \(V(\mathcal{M})\) is a mapping from normalized path to the body extracted from the last matching occurrence.

A complete assistant FILE block consists of a path line and a closed code fence. A truncated or malformed fragment is not treated as a complete block. Content hashes are computed over the normalized extracted body and compared with the corresponding current workspace file. The primary efficiency measure is mean prompt tokens per episode. The primary capability measure is episode success rate (ESR) under the frozen step-level evaluator.

## 3.2 Processing order
The implementation follows this order:

1. Select and trim the history inputs.
2. Optionally apply S1 to assistant FILE blocks in the history.
3. Construct candidate visibility proofs from the projected history using the same file extractor.
4. Assemble the current request, including must-include files, edit targets, candidate-full files, and other policy-selected context.
5. Run VP over the concrete final message list.
6. If verification fails, rebuild the request with the failing files fully re-injected and verify again.
7. If the second check still fails, mark the request insufficient and do not call the model.
8. If the check passes, call the model and apply returned file blocks to the workspace.
S1 therefore runs before proof construction and message assembly. VP runs after assembly, at the final-message boundary.

## 3.3 Visibility Proof (VP)
For every \(p\in\mathcal{O}_t\), VP requires both:

\[ p\in V(\mathcal{M}_t) \quad\text{and}\quad \operatorname{SHA256}(V(\mathcal{M}_t)[p])=h_{W_t}(p). \]

For every \(p\in E_t\cup C_t\), VP additionally requires a complete file block in the current user-context message whose hash matches the current workspace. Historical visibility alone does not satisfy this latter condition.

If a check fails, the assembler forces full delivery of the failing path or paths and reconstructs the request. The verifier then checks the rebuilt messages. A persistent failure results in an INSUFFICIENT state and the model call is skipped.

Scope of the check. The checked set is determined by the system's own omission, edit-target, and candidate-full bookkeeping. VP does not prove that this bookkeeping identified every file required by the task. It does not establish semantic completeness of non-file text, validate arbitrary message formats, or guarantee that every relevant requirement is represented in the prompt. It also does not eliminate a time-of-check/time-of-use race between verification and the subsequent HTTP request; the evaluated implementation does not hold a cross-process lock through transmission. Controlled fault-injection results should not be interpreted as estimates of natural production fault rates.

## 3.4 Verified History Projection (S1)
At each editing step, an assistant may emit a complete replacement body for a file. Later messages may emit another complete body for the same path. Retaining every version increases prompt length, even though the verifier's path map uses only the last complete matching block for each path.

S1 processes only messages with role=assistant and complete assistant FILE blocks. For each normalized path, it identifies the complete blocks in message order. In the confirmatory first_last configuration, it retains the first and last complete block and replaces intermediate complete blocks with a short fold marker. The marker contains neither the FILE: prefix nor a matching code fence, so the extractor does not interpret it as a file body. Non-assistant messages and content outside the matched complete blocks are left unchanged.

The first block is retained as an additional trajectory endpoint; the last block is mandatory for the preservation property. S1 is deterministic and does not invoke an additional language model.

## 3.5 Projection-preservation proposition
Let \(V\) be the path-keyed, last-write-wins extractor defined in §3.1. Let \(P\) be a projection that, for every path occurring in a history \(H\), retains that path's last complete assistant FILE block and replaces only earlier complete blocks with non-matching markers.

Proposition. Under the specified extractor and block-matching rules,

\[ V(P(H))=V(H). \]

Proof sketch. For each normalized path, the value assigned by \(V\) is the body of the last complete matching block encountered in scan order. Projection \(P\) retains that block and removes only earlier matching blocks for the same path. Because fold markers do not match the extractor, they cannot introduce a new value or overwrite the retained block. The final value for every path is therefore unchanged. The first_last configuration retains an additional earlier block but still retains the last block, so it satisfies the same condition. \(\square\)

This is a constructive argument relative to the implemented extractor and projection rule. It is not a theorem over arbitrary message languages, arbitrary parsers, or all semantic information in a conversation. The argument also does not imply that intermediate file bodies are semantically redundant for every possible future task; those bodies are removed from the transcript.

## 3.6 Auxiliary obligation ledger (S2) and implementation cost
The SAH configuration additionally renders rule-based open-obligation reminder lines (S2). S2 is treated as an auxiliary heuristic, not as a core contribution or a verified semantic completion detector. Its state transitions can close obligations based on syntactic or file-change cues that do not necessarily establish semantic completion. Because the confirmatory design does not include an F+S2-only arm, the independent effect of S2 cannot be identified from SAH−F.

S1 requires a scan of assistant message contents and a path-indexed dictionary; VP scans the final messages and hashes the files in its check scope. Their costs are linear in the amount of text scanned, plus the cost of hashing checked file bodies. The experiments report prompt-token counts and do not measure end-to-end latency, server-side prefill time, or KV-cache memory.

# 4. Experimental Setup
## 4.1 Research questions
- RQ1 — Context efficiency: How does VAM-Coder’s selective-delivery strategy compare with alternative context-management policies in prompt-token consumption?
- RQ2 — Task capability: What efficiency–success-rate trade-off is observed when context volume is reduced, and does PROJ meet the prespecified −12 pp ESR non-inferiority margin relative to F?
- RQ3 — Delivery reliability: Does VP make the expected decisions and trigger the specified recovery or fail-closed behavior under controlled visibility, version, history, and budget faults?
- RQ4 — Mechanism contribution: What incremental effect is associated with S1, and how robust are the primary findings across model families and post-hoc archetype-cluster sensitivity analyses?
## 4.2 Models, tasks, and configurations
The confirmatory evaluation used deepseek-v4.1-flash-1017 and qwen3-coder-flash, accessed through the same OpenAI-compatible MaaS endpoint. Both used temperature 0, seed 0, and a maximum generation length of 2,048 tokens. The task set contained 56 multi-step repository-editing tasks: 48 independent tasks arranged as 24 archetypes with two task variants each, plus eight dose tasks treated as singleton clusters in the cluster sensitivity analysis.

Each model was evaluated on seven arms with three repetitions per task–arm combination, giving 168 episodes per arm and 1,176 episodes per model. The statistical unit for the prespecified paired comparisons was the task, not the individual episode; each task-level arm value was the mean across its three repetitions.

The principal configurations were:

- F: the selective-delivery baseline with full history retention and no S1 or S2;
- PROJ: F plus S1 only;
- SAH: F plus S1 and the auxiliary S2 obligation ledger.
The alternative context-policy comparison arms were TRUNC, a sliding-window history policy with a 1,300-character per-step budget; SUMM, a same-model summarization baseline whose summarizer prompt cost was included in the prompt accounting; and RETR, a BM25 top-three retrieval policy that retained the latest history. memory_off was included as an additional reference arm. These external baselines were reimplementations for this experiment, not the original authors' implementations.

PROJ−F is the direct estimate of S1 added to F. SAH−F estimates the combined F+S1+S2 configuration and must not be interpreted as the independent effect of S2.

## 4.3 Metrics and statistical analysis
The primary efficiency metric was mean prompt tokens per episode. The primary capability metric was ESR, defined as the proportion of episodes satisfying the frozen evaluator. The non-inferiority margin was −12 percentage points for ESR.

For each model, paired differences were computed over 56 tasks after averaging repetitions within each task and arm. Confidence intervals used task-level bootstrap resampling with seed 20261102 and 10,000 replicates. Two-sided sign-flip tests and Holm correction were applied within the prespecified comparison families. Non-inferiority was declared when the lower bound of the 95% confidence interval for the ESR difference was at least −12 pp. Episode counts are reported to describe execution volume, not as the independent sample size for the paired tests.

The archetype-cluster bootstrap (5,000 replicates) and leave-one-archetype-out analysis were conducted after the primary analysis and are reported as sensitivity analyses, not as preregistered confirmatory tests. The main cluster analysis used 32 clusters: 24 independent-task archetypes, each containing two tasks, and eight dose-task singleton clusters.

## 4.4 VP fault-injection protocol
Phase 1 comprised 31 deterministic scenarios: 13 negative fault scenarios, nine ordinary positive scenarios, eight false-block controls, and one boundary scenario (C4). The boundary scenario allowed omission of optional content only when must-include content remained present. Accordingly, the safe-omission rate denominator was 10 (nine positive scenarios plus C4). The phase compared VP with a content-hash baseline (B1) and an ever-sent cache baseline (B2).

Phase 2 embedded 10 frozen scenarios in a real runner using test-side monkeypatching and three repetitions per scenario (30 executions) on DeepSeek. The production code was not modified. The phase was evaluated as a set of per-scenario assertions, not as a statistical generalization study.

# 5. Historical Validation of the Earlier V12-F Configuration
This section reports the earlier P1 confirmation batch for the `vam_coder_v1.2_F` configuration (hereafter V12-F). It is presented as historical validation of the selective-delivery baseline that preceded the V13E study. It is not part of the V13E confirmatory batch, does not share its task set or model configuration, and is not pooled with the 56-task V13E analysis. The P1 results support the efficiency and capability-retention profile of V12-F under its own preregistered protocol; they do not isolate the incremental contribution of the later VP final-message verifier.

## 5.1 Protocol and execution
P1 used the `deepseek-v4.1-flash-1017` model through an OpenAI-compatible MaaS endpoint, with temperature 0, seed 0, and a 2,048-token generation limit. The frozen task suite contained 48 repository-editing tasks from eight parameterized task families: 16 short tasks (two steps each), 16 medium tasks (five steps each), and 16 long tasks (ten steps each), for 272 task steps in total. Each of three architectures was run five times per task, yielding 240 episodes per architecture and 720 episodes overall. The recorded execution comprised 4,080 step rows and 4,080 model requests. The three architectures were V12-F (`vam_coder_v1.2_F`), `memory_off`, and `symbol_full_read`.

The primary efficiency measure was mean prompt tokens per episode. Episode success rate (ESR) was the primary capability measure. The preregistered non-inferiority margin for ESR was −12 percentage points (pp). Paired comparisons used task-level clustering; bootstrap confidence intervals used 10,000 replicates with seed 20261102 and task ID as the resampling cluster. Two primary comparisons were specified, with Holm correction applied to the corresponding sign-flip tests. The eight task-family sensitivity analysis was reported separately.

## 5.2 Primary efficiency and capability results
V12-F used 2,510.2 prompt tokens per episode on average, compared with 3,287.2 for `memory_off` and 3,311.4 for `symbol_full_read`. The corresponding ESR values were 92.92% (223/240), 93.75% (225/240), and 93.75% (225/240), respectively. Thus, V12-F reduced mean prompt tokens by 23.6% relative to `memory_off` and by 24.2% relative to `symbol_full_read`, while its observed ESR was 0.83 pp lower than either reference arm.

Table 1 summarizes the architecture-level results. TPAE denotes total prompt-plus-completion tokens per episode; TPSE denotes total tokens per successful episode. The reported standard deviations describe episode-level prompt-token variation, not uncertainty in the paired task-level treatment effect.
Table 1. P1 architecture-level results. ESR is the proportion of successful episodes; TPAE and TPSE are token counts per episode.
The paired V12-F minus reference-arm prompt-token differences were −777.0 tokens per episode (95% CI [−974.8, −584.4]) against `memory_off` and −801.2 tokens (95% CI [−1,003.3, −603.3]) against `symbol_full_read`. The corresponding TPAE differences were −786.6 (95% CI [−979.3, −601.8]) and −845.3 (95% CI [−1,058.7, −640.1]). Both prompt-token sign-flip tests remained significant after Holm correction (adjusted p = 0.0002 for each comparison). At the task-family level, all eight family-mean prompt differences were negative for both primary comparisons (family sign-flip p = 0.0079 and 0.0072, respectively).

For capability, the ESR difference was −0.83 pp for V12-F versus `memory_off` (95% CI [−4.17, +2.92] pp) and −0.83 pp versus `symbol_full_read` (95% CI [−5.42, +2.92] pp). Both lower confidence bounds were above the prespecified −12 pp non-inferiority margin. The non-inferiority criterion was therefore met for both comparisons. These results do not establish ESR superiority: both intervals include zero, and the preregistered analysis did not make an ESR superiority claim.

Table 2 reports the paired primary contrasts. Negative token differences favor V12-F; negative ESR differences indicate a lower observed success rate for V12-F.
Table 2. P1 preregistered paired comparisons. Confidence intervals are task-cluster bootstrap intervals; the ESR margin was −12 pp.
The observed prompt savings increased with task length. Mean prompt tokens were 624.0 for V12-F versus 748.6 for `memory_off` on short tasks, 1,792.1 versus 2,264.5 on medium tasks, and 5,114.6 versus 6,848.5 on long tasks. The long-task difference was 1,733.9 tokens per episode (approximately 25.3%). This pattern is consistent with savings accumulating as repeated full-context overhead grows across longer trajectories.

There were 47 failed episodes across the three architectures. One short-task variant (`p1_S03c`) failed in all 15 repetitions across all three architectures; it was retained in the ESR denominator as required by the preregistered rules. Protocol violations were also recorded (2 for V12-F, 6 for `memory_off`, and 4 for `symbol_full_read`) and counted as failures. V12-F had zero INSUFFICIENT steps and zero delivery-hazard events under the P1 accounting. These details matter because the aggregate ESR differences are small and the task set contains a concentrated failure mode.

P1 therefore provides historical evidence that V12-F reduced prompt and total-token consumption while meeting the prespecified ESR non-inferiority criterion on this single-model, parameterized 48-task suite. Its scope is limited by the eight shared task families, one hosted model endpoint, and the retained protocol violations. It should not be interpreted as independent evidence for every later VP component, as a cross-provider replication, or as evidence of latency or KV-cache improvements.

The P1 batch is reported separately from V13E. Its 48-task design, five repetitions, model configuration, and baseline architecture differ from the V13E confirmatory design (56 tasks, three repetitions, two model families). No episodes, task-level estimates, or confidence intervals are pooled across the two studies.

# 6. Confirmatory Evaluation of VAM-Coder (V13E)
## 6.1 Selective-delivery baseline (F)
Within the V13E confirmatory batch, F is the selective-delivery baseline against which PROJ and SAH are compared. The earlier V12-F P1 validation is reported separately in Section 5 and is not pooled with the V13E task-level analysis. The F-versus-PROJ comparison therefore estimates the incremental effect of S1 in the V13E configuration, not the historical P1 effect.

## 6.2 Omission/reuse mechanism ablation (P2)
In the 1,680-episode P2 ablation batch, disabling the VP omission/reuse path increased prompt cost by 397.6 tokens per episode relative to F (no-VP minus F; 95% CI [275.4, 524.8]). The corresponding ESR difference was +0.42 pp (no-VP minus F; 95% CI [−2.08, +2.92] pp), with the interval crossing zero. This should be described as no detectable ESR difference under this ablation, not as evidence that the ESR values are identical.

This ablation identifies the cost contribution of the VP omission/reuse path in the P2 configuration. It does not isolate the VP final-message verifier from every other component of that path, and it is not an S1 ablation. History redaction also reduced prompt volume but adversely affected visible-context recall, while the must-closure ablation had a comparatively small prompt effect. These findings motivated the later separation of delivery reuse from historical file-body projection.

**Figure 5. P2 mechanism ablation. Both panels use the same difference direction: no-VP minus F. The prompt-cost increase is +397.6 tokens per episode (95% CI [275.4, 524.8]); the ESR difference is +0.42 pp (95% CI [−2.08, +2.92] pp), which crosses zero. The paired unit is the task; the bootstrap used 10,000 replicates and seed 20261102.**

## 6.3 VP controlled fault-injection results
In Phase 1, all 31 scenarios received their expected decisions. The unsafe-omission rate was 0/13, the safe-omission rate was 10/10 (nine ordinary positive cases plus the C4 boundary case), the false-block rate was 0, and the fallback-success rate was 13/13. The joint prespecified engineering threshold was met. The mechanism comparison on visibility scenarios V1–V5 produced detection rates of 1.00 for VP, 0.00 for B1, and 0.80 for B2. VP's exclusive detection occurred in V4, where the content hash remained valid and the file had previously been sent, but the corresponding block was absent from the final messages.

In Phase 2, the expected decision was observed in all 30 executions across 10 scenarios, with zero unsafe shipments and zero delivery-omission-hazard events under the frozen accounting rule. Positive scenarios P1 and P5 correctly allowed omission; negative scenarios triggered full delivery or an insufficient/no-request decision as specified. The phase therefore tests both refusal and successful reuse behavior.

An initial set of 18 executions was retained as superseded after a task-mapping issue was found to make some injected omissions unreachable. The final 30-execution set used corrected task mappings; the superseded records remain archived and are excluded from the final result. The results support VP behavior under the tested controlled injections. They do not estimate production fault rates or establish universal safety.

## 6.4 Main confirmatory comparison: S1-only PROJ versus F
Each arm contained 168 episodes per model. The paired task-level analysis used 56 tasks.


S1-only efficiency. PROJ reduced prompt tokens relative to F by 678.7 tokens per episode on DeepSeek (95% CI [−960.7, −431.2]), corresponding to an 18.1% reduction. On Qwen, the reduction was 685.0 tokens (95% CI [−949.4, −442.3]), or 18.3%. Both confidence intervals were strictly below zero.

S1-only capability. The PROJ−F ESR difference was −5.4 pp on DeepSeek (95% CI [−10.1, −1.2] pp) and +2.4 pp on Qwen (95% CI [−0.6, +6.0] pp). Both lower confidence bounds exceeded the −12 pp non-inferiority margin. The DeepSeek result nevertheless represents a measurable ESR decrease and has less margin headroom than the Qwen result. We therefore interpret the finding as non-inferiority under the prespecified margin, not as unchanged or improved capability.

Combined SAH configuration. SAH−F reduced prompt tokens by 632.6 (95% CI [−885.7, −403.5]; 16.9%) on DeepSeek and 697.3 (95% CI [−969.7, −446.7]; 18.6%) on Qwen. ESR differences were −1.2 pp (95% CI [−5.4, +3.0] pp) and +1.8 pp (95% CI [−0.6, +5.4] pp), respectively. These results describe F+S1+S2 as a combined configuration. Because the experiment did not include an F+S2-only arm, they do not identify an independent S2 effect.

**Figures 1 and 2. Figure 1 reports prompt tokens per episode; Figure 2 reports ESR on an untruncated 0–100% scale. Error bars are 95% task-level bootstrap intervals. The model panels are reported separately and are not pooled.**

**Figure 1. Prompt tokens per episode for F, PROJ, and SAH. Points are means of task-level means; whiskers are 95% task-bootstrap confidence intervals (seed 20261102; 10,000 replicates). DeepSeek and Qwen are shown separately. PROJ−F is the direct S1-only comparison; SAH additionally includes S2.**

**Figure 2. Episode success rate for F, PROJ, and SAH. The vertical axis spans 0–100% and is not truncated. Whiskers are 95% task-bootstrap confidence intervals. The DeepSeek PROJ decrease is visible and should not be interpreted as a zero-cost capability change.**
## 6.5 External context-management baselines
TRUNC achieved the lowest prompt-token mean among the compared methods (DeepSeek 2,456.4; Qwen 2,347.2), but it does so by discarding older history without VP's delivery check. SAH was non-inferior to TRUNC on ESR under the prespecified margin, but it was not cheaper in prompt tokens. The paired SAH−TRUNC ESR differences were +0.6 pp (95% CI [−1.8, +3.0] pp) on DeepSeek and 0.0 pp (95% CI [−3.6, +3.6] pp) on Qwen. Thus, the proposed configuration does not dominate all alternatives on every metric.


SAH used 1,891.6 fewer prompt tokens than SUMM on DeepSeek (95% CI [−2,575.7, −1,261.1]) and 1,205.9 fewer on Qwen (95% CI [−1,595.9, −832.5]). The descriptive SAH−RETR differences were −153.6 tokens (95% CI [−251.6, −58.7]) and −133.0 tokens (95% CI [−220.5, −48.5]), respectively; these are not promoted to primary Holm-gated claims.

SUMM had the highest prompt cost once summarizer prompt tokens were included in the accounting (DeepSeek 5,006.5; Qwen 4,248.7). The auxiliary-token column is a decomposition of summarizer overhead and must not be added again to the reported prompt mean. SAH used fewer prompt tokens than SUMM in both models. RETR fell between the core configurations and the other baselines; SAH−RETR prompt differences are reported descriptively rather than as a primary Holm-gated claim.


**Figure 3. Prompt tokens per episode for the six compared context-management methods. Bars show episode means; whiskers show 95% task-bootstrap intervals. The zero-based vertical axis preserves TRUNC's lower prompt cost. SUMM prompt accounting includes the summarizer prompt overhead; auxiliary tokens are shown only as a decomposition and are not added a second time.**

**Figure 4. Efficiency–capability plane. The horizontal axis is prompt tokens per episode (lower is better); the vertical axis is ESR (higher is better) and spans 0–100%. Points are episode means with task-bootstrap uncertainty intervals. The figure is descriptive; it does not establish a universal ranking across models or workloads.**
## 6.6 Cross-model consistency
The directions of the primary PROJ−F prompt comparisons were consistent across DeepSeek and Qwen, and both models met the ESR non-inferiority criterion. Absolute ESR levels differed substantially between the models, so the results are reported separately rather than pooled. The replication supports directional consistency across these two model families, but it is not a multi-provider replication because both models were accessed through the same MaaS endpoint.

## 6.7 Archetype-cluster sensitivity analysis
The post-hoc cluster bootstrap resampled 32 clusters: 24 independent-task archetypes (two task variants per archetype) and eight dose-task singletons. Across the four primary prompt comparisons (DeepSeek/Qwen × PROJ−F/SAH−F), all cluster-bootstrap confidence intervals remained strictly below zero. For DeepSeek, the cluster interval was [−1,050.9, −340.5] for PROJ−F and [−977.1, −317.1] for SAH−F. The lower confidence bounds for all ESR non-inferiority comparisons remained above −12 pp; the tightest was DeepSeek PROJ−F at approximately −9.6 pp. Leave-one-cluster-out analyses did not reverse the prompt-saving direction or produce a non-inferiority failure.

The cluster-bootstrap intervals for prompt differences were approximately 1.34–1.39 times wider than the task-level intervals, indicating that task-level resampling understates uncertainty when tasks share archetypes. The cluster analysis is a post-hoc sensitivity check, not a replacement for the preregistered task-level analysis and not an increase in the number of independent tasks.


**Figure 6a. Prompt-token differences for PROJ−F and SAH−F. Task-level paired bootstrap intervals are the preregistered confirmatory intervals; archetype-cluster intervals and leave-one-cluster-out ranges are post-hoc sensitivity results. The 32 clusters comprise 24 independent-task archetypes and eight dose singletons.**

**Figure 6b. ESR differences in percentage points, with the −12 pp non-inferiority margin. Task-level intervals are confirmatory; cluster-bootstrap and leave-one-cluster-out results are sensitivity analyses. DeepSeek PROJ−F is the closest primary comparison to the non-inferiority margin.**
## 6.8 Supporting and negative evidence
A separate offline replay used a historical V13B DeepSeek run containing 504 episodes and 2,808 steps. The replay applied the default last-only projection and found zero mismatches in the extracted file map and pre-send fields. The confirmatory V13E runs used first_last, which retains the same last block plus the first block; the preservation proposition applies to both because both retain the last complete block. The replay should therefore be interpreted as empirical support for the shared last-block invariant, not as a separate replay of the exact confirmatory first_last configuration.

A dedicated dual-token experiment did not establish an independent contribution under its frozen decision rules and is not used as evidence for the present method. Other exploratory branches are likewise excluded from the confirmatory claims.

# 7. Transfer Evaluation on a SWE-bench Lite Subset (P1_TRANSFER)
## 7.1 Evaluation scope and protocol
A separate transfer evaluation used a 10-instance subset of the SWE-bench Lite test split. The selected instances were requests-3362, requests-863, requests-1963, pytest-7432, pytest-11143, pytest-5413, pytest-6116, flask-4045, flask-5063, and pylint-7993. The evaluation used local Docker execution and FAIL_TO_PASS tests; it was not conducted under the official full SWE-bench leaderboard protocol. The subset was selected toward bounded patches and lighter environments, with at most three instances per repository and between one and twelve FAIL_TO_PASS tests per instance.

Three context-policy arms were evaluated: F, the VAM-Coder selective-delivery baseline; PROJ, the VAM-Coder configuration combining F with S1 in first_last mode; and MOFF, a full-repository context policy that injected the repository at each step. MOFF is an alternative context-management policy, not a complete external coding agent. Each model evaluated 10 instances × 3 arms × 3 repetitions, yielding 90 episodes per model and 180 across both models. The statistical unit was the instance (n=10); repetitions were averaged within each instance before paired bootstrap analysis.

The DeepSeek model was deepseek-v4.1-flash-1017. The Qwen transfer model was qwen3.8-flash, which differs from qwen3-coder-flash used in the V13E confirmatory study because the original token-plan endpoint was unavailable. The runs used temperature 0, seed 0, max_tokens 16,384, a 16,384-token budget, and a 65,536-token context window. Qwen timeout handling was changed from 600 to 1,200 seconds with thinking disabled after initial timeouts; the final run had no timeouts. Some DeepSeek completion reruns used a token-plan endpoint with the same model ID. For each model, flask-5063 F and PROJ episodes encountered REQUIRED_CONTEXT_EXCEEDS_LIMIT and were retained as ESR failures under the frozen no-retry rule.

## 7.2 Prompt efficiency and episode success
For DeepSeek, F achieved an ESR of 80.0% (24/30) with approximately 24.1k mean prompt tokens, PROJ achieved 83.3% (25/30) with approximately 24.1k tokens, and MOFF achieved 93.3% (28/30) with approximately 474k tokens. For Qwen 3.8, F achieved 86.7% (26/30) with approximately 24.1k tokens, PROJ achieved 86.7% (26/30) with approximately 24.1k tokens, and MOFF achieved 100% (30/30) with approximately 518k tokens.

Relative to MOFF, PROJ reduced observed prompt-token volume by approximately 95.0% for DeepSeek and 95.3% for Qwen. The paired PROJ−MOFF prompt differences were approximately −452k tokens (95% CI [−593k, −311k]) and −496k tokens (95% CI [−642k, −345k]), respectively. However, MOFF had higher observed ESR in both model runs. The ESR differences for PROJ−MOFF were −10 percentage points (95% CI [−33, +7]) for DeepSeek and −13 pp (95% CI [−33, 0]) for Qwen. The wide intervals and small number of instances preclude a strong capability conclusion.

PROJ did not show an incremental prompt-token reduction over F in this single-step transfer setting: the observed difference was approximately zero for DeepSeek and +1 token for Qwen, with confidence intervals spanning zero. This is consistent with the task format providing limited opportunity for S1 to remove accumulated multi-turn file history. The transfer result therefore supports the selective-delivery versus full-repository-injection comparison, but does not establish an additional S1 benefit in this setting.

## 7.3 Interpretation and limitations
The transfer experiment demonstrates a pronounced prompt-volume difference between selective delivery and full-repository injection on the selected subset, accompanied by a lower observed success rate for the selective configurations. It should therefore be interpreted as an efficiency–capability trade-off rather than dominance by VAM-Coder. It also does not compare VAM-Coder with complete systems such as SWE-agent or OpenHands. The result is limited by the 10-instance subset, single-step full-file task format, model replacement for Qwen, execution deviations, and small instance-level sample size. The task format does not recreate long multi-turn histories in which S1 is expected to have its greatest effect.

The API cached_tokens field was recorded but is not a measurement of server-side KV-cache memory. No claims about KV-cache capacity, prefill latency, end-to-end latency, or serving cost are drawn from these values. The transfer study is reported separately from V13E and is not pooled with the 56-task confirmatory analysis.

# 8. Discussion and Threats to Validity
## 8.1 What the results establish
The main result is that path-based projection can reduce prompt transmission while preserving the file map used by a final-message verifier, under a specified parser and retention rule. In the S1-only PROJ arm, prompt tokens decreased by approximately 18% relative to F on both evaluated models. The ESR result was non-inferior under the prespecified −12 pp margin, although the DeepSeek point estimate decreased by 5.4 pp. This trade-off is important: the method reduces prompt volume, but the evidence does not support a claim that S1 is capability-neutral in every model or task.

VP addresses a different part of the problem. It does not select what to remember; it checks whether files whose omission is being relied upon are actually present and version-consistent in the final request. The V4 comparison illustrates why a content hash or an ever-sent cache record is insufficient by itself: a file can be unchanged and previously transmitted while absent from the final messages. Under the controlled scenarios tested here, VP detected that condition and triggered the expected recovery behavior.

## 8.2 Relationship to other context-management methods
TRUNC remains the lowest-prompt method in the same-batch comparison, which shows that VP+S1 is not a token-minimization optimum. Its design objective is different: it reduces repeated file bodies while retaining a check on the delivery of in-scope omitted files. SUMM incurs additional summarizer prompt overhead in this accounting, while RETR trades full history for selected retrieved messages. These baselines are reimplementations and should not be treated as exact replications of their original systems.

The method is complementary to work on asynchronous compaction and prefix-cache preservation. Those systems address when compaction runs and how serving overhead is managed; our experiments address file visibility and version consistency at the final-message boundary. Because no latency, prefill, or KV-cache measurements were collected, the present results cannot establish serving-level efficiency.

## 8.3 Limitations and threats to validity
First, the task suite consists of controlled micro-repository editing tasks rather than full-scale industrial repositories or a broad benchmark such as SWE-bench. The results may not transfer to larger repositories, different agent scaffolds, or workloads dominated by non-file tool outputs.

Second, the confirmatory evaluation covers two model families accessed through one compatible MaaS endpoint. This is evidence of directional consistency, not independent replication across providers. Hosted APIs may also exhibit nondeterminism even at temperature zero; repetitions were therefore averaged within task, and task was treated as the statistical unit.

Third, the task set contains shared archetypes. The post-hoc cluster analysis widens prompt confidence intervals by approximately 34–39% but does not reverse the primary directions. The cluster analysis is sensitivity evidence and was not preregistered.

Fourth, the S1 preservation argument is relative to a particular regular-expression extractor, path normalization, complete-block grammar, and last-write-wins map. It does not guarantee semantic equivalence of the full conversation. The offline replay used a separate historical V13B trace and the last-only mode, whereas the confirmatory V13E runs used first_last; the formal condition is shared, but the empirical replay did not independently rerun the exact confirmatory mode.

Fifth, VP's check scope depends on the system's prior identification of omitted files and edit targets. It cannot prove that the system discovered every task-relevant file. The implementation also lacks a lock spanning verification and HTTP transmission, leaving a time-of-check/time-of-use window.

Sixth, Phase 1 and Phase 2 are controlled fault-injection tests. Their zero unsafe-ship count applies only to the frozen scenarios and executions. It is not an estimate of production failure probability or a universal safety guarantee. The Phase-2 evidence is from one model family.

Finally, S2 is a rule-based auxiliary heuristic with known semantic limitations, and the design lacks an F+S2-only arm. No independent S2 contribution is claimed. External baselines are local reimplementations, and their parameterization may differ from the original systems.

## 8.4 Practical implications
For coding-agent systems that omit files because they are believed to have been delivered earlier, a final-message verifier can make that assumption explicit and testable. For histories dominated by repeated complete-file rewrites, path-based projection can remove intermediate bodies while preserving the file map consumed by that verifier. These mechanisms should be deployed with explicit check scopes, robust request serialization, and monitoring for races between verification and transmission.

# 9. Conclusion
This paper presented VAM-Coder, a verifiable context-management strategy for multi-turn coding agents. VAM-Coder combines selective context delivery with Verified History Projection (S1) and a final-request Visibility Proof (VP). S1 reduces repeated complete assistant file blocks while preserving the path-keyed, last-write-wins file mapping consumed by the verifier under the specified extraction rules. VP checks that in-scope files whose omission is relied upon remain completely visible and version-consistent in the concrete request, with reinjection and re-verification on failure and fail-closed behavior when verification remains unsatisfied. In the 56-task V13E confirmatory study, PROJ reduced prompt tokens relative to F by 18.1% on DeepSeek and 18.3% on Qwen, meeting the prespecified −12 pp ESR non-inferiority margin; the DeepSeek ESR point estimate nevertheless decreased by 5.4 pp. The separate P1_TRANSFER subset showed approximately 95% lower prompt volume for PROJ than full-repository injection, while MOFF achieved higher observed ESR. Controlled VP fault-injection tests produced the expected decisions in the tested scenarios. Taken together, the evidence supports VAM-Coder as a context-management strategy that can reduce redundant context transmission while making selected omission assumptions explicit and testable. The findings do not establish universal task superiority, semantic equivalence of arbitrary histories, unrestricted safety, or improvements in latency, prefill time, or server-side KV-cache behavior.

# References
[1] Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang. Lost in the Middle: How Language Models Use Long Contexts. Transactions of the Association for Computational Linguistics, 12:157–173, 2024. arXiv:2307.03172.

[2] Hsieh et al. RULER: What's the Real Context Size of Your Long-Context Language Models? Proceedings of COLM, 2024. arXiv:2404.06654.

[3] Yushi Bai et al. LongBench: A Bilingual, Multitask Benchmark for Long Context Understanding. Proceedings of ACL, 2024. arXiv:2308.14508.

[4] Yue Xue. When and How Context Rot Appears in Coding Agents: A White-Box Study of Agent Skills in Code Auditing. arXiv:2607.17937, 2026.

[5] Shijie Xia, Yikun Wang, Zhen Huang, and Pengfei Liu. Diagnosing and Mitigating Context Rot in Long-horizon Search. arXiv:2606.29718, 2026.

[6] Charles Packer et al. MemGPT: Towards LLMs as Operating Systems. arXiv:2310.08560, 2023.

[7] Joon Sung Park et al. Generative Agents: Interactive Simulacra of Human Behavior. Proceedings of UIST, 2023. arXiv:2304.03442.

[8] Noah Shinn et al. Reflexion: Language Agents with Verbal Reinforcement Learning. Advances in Neural Information Processing Systems, 2023. arXiv:2303.11366.

[9] Guanzhi Wang et al. Voyager: An Open-Ended Embodied Agent with Large Language Models. arXiv:2305.16291, 2023.

[10] Zepeng Zhang et al. A Survey on the Memory Mechanism of Large Language Model Based Agents. arXiv:2404.13501, 2024.

[11] Jinghao Luo, Yuchen Tian, Chuxue Cao, Ziyang Luo, Hongzhan Lin, Kaixin Li, Chuyi Kong, Ruichao Yang, and Jing Ma. From Storage to Experience: A Survey on the Evolution of LLM Agent Memory Mechanisms. Findings of the Association for Computational Linguistics: ACL 2026, 41622–41652, 2026. DOI: 10.18653/v1/2026.findings-acl.2069.

[12] Mingyu Zhang, Zixu Li, Zhiheng Fu, Zhiwei Chen, Jinhe Bi, and Yupeng Hu. TrawMem: Reframing Agent Memory as Task-Oriented Role-Adaptive Workspaces. arXiv:2610.36918, 2026.

[13] Yuyao Wang, Zhongjian Zhang, Mo Chi, Kaichi Yu, Yuhan Li, Miao Peng, Bing Tong, Chen Zhang, Yan Zhou, and Jia Li. EvoMemBench: Benchmarking Agent Memory from a Self-Evolving Perspective. arXiv:2605.18421, 2026.

[14] Huiqiang Jiang et al. LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models. Proceedings of EMNLP, 2023. arXiv:2310.05736.

[15] Yuhui Li et al. Compressing Context to Enhance Inference Efficiency of Large Language Models (Selective Context). Proceedings of EMNLP, 2023. arXiv:2310.06201.

[16] Shamin Chokshi. Lexical Prompt Compression for Large Language Models: A Training-Free, Deterministic Pipeline with Empirical Pareto Analysis Across Eleven Task Categories. arXiv:2609.13154, 2026.

[17] Haoran Zhang and Zhaohua Sun. AGORA: Adapter-Grounded Observation-Action Retention for Inference-Free Prompt Compression in LLM Agents. arXiv:2605.26596, 2026.

[18] Carlos E. Jimenez et al. SWE-bench: Can Language Models Resolve Real-World GitHub Issues? International Conference on Learning Representations, 2024. arXiv:2310.06770.

[19] John Yang et al. SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering. Advances in Neural Information Processing Systems, 2024. arXiv:2405.15793.

[20] X. Zhang et al. AutoCodeRover: Autonomous Program Improvement. Proceedings of ISSTA, 2024. arXiv:2404.05427.

[21] Shuyan Wang et al. OpenHands: An Open Platform for AI Software Developers as Generalist Agents. International Conference on Learning Representations, 2025. arXiv:2407.16741.

[22] Han Li, Letian Zhu, Bohan Zhang, Rili Feng, Jiaming Wang, Yue Pan, Earl T. Barr, Federica Sarro, Zhaoyang Chu, and He Ye. ContextBench: A Benchmark for Context Retrieval in Coding Agents. arXiv:2602.05892, 2026.

[23] Luis Gaspar Schroeder, Aditya Desai, Alejandro Cuadron Lafuente, Kyle Chu, Shu Liu, Mark Zhao, Stephan Krusche, Alfons Kemper, Matei Zaharia, and Joseph E. Gonzalez. vCache: Verified Semantic Prompt Caching. International Conference on Learning Representations, 2026. arXiv:2502.03771.

[24] Chenchen Gu, Xiang Lisa Li, Rohith Kuditipudi, Percy Liang, and Tatsunori Hashimoto. Auditing Prompt Caching in Language Model APIs. Proceedings of the 42nd International Conference on Machine Learning, PMLR 267:20477–20496, 2025. arXiv:2502.07776.

[25] Woosuk Kwon et al. Efficient Memory Management for Large Language Model Serving with PagedAttention. Proceedings of SOSP, 2023. arXiv:2309.06180.

[26] Minki Kang, Wei-Ning Chen, Dongge Han, Huseyin A. Inan, Lukas Wutschitz, Yanzhi Chen, Robert Sim, and Saravan Rajmohan. ACON: Optimizing Context Compression for Long-horizon LLM Agents. Proceedings of the 43rd International Conference on Machine Learning, PMLR 306:55321–55375, 2026. arXiv:2510.00615.

[27] Ruopei Sun, Jianfeng Cai, Kangwen Zhao, Wengang Zhou, and Houqiang Li. Compact-Bench: Measuring What Context Compaction Costs Long-Horizon Coding Agents. arXiv:2610.31710, 2026.

[28] Le Chen, Zishen Wan, Baixi Sun, Xiaolong Ma, Chih-Hsuan Yang, Feng Yan, Sheng Di, Franck Cappello, and Rajeev Thakur. Measure Before You Manage: Evaluating Agent Working Memory in Coding Agents. arXiv:2608.31057, 2026.

[29] Ritul Satish, Prasoon Sinha, Akiho Kawada, and Neeraja J. Yadwadkar. Beyond Token Savings: A Systematic Study of Context Compression in LLM Agents. arXiv:2609.32961, 2026.

[30] Shantanu Dixit, Anson Bastos, Xuchao Zhang, Chetan Bansal, and Saravan Rajmohan. FOCUS: Training-Free Decision-Preserving Context Compression for LLM Agents. arXiv:2609.37590, 2026.

[31] Banruo Liu, Haoran Qiu, Íñigo Goiri, Jingran Zhou, Rodrigo Fonseca, Ricardo Bianchini, Fan Lai, and Esha Choukse. Benchmarking Long-Horizon Agent Context Compaction with CompactionBench. Microsoft Research preprint, 2026.

[32] Patrick Lewis et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. Advances in Neural Information Processing Systems, 2020. arXiv:2005.11401.

[33] Yunfan Gao et al. Retrieval-Augmented Generation for Large Language Models: A Survey. arXiv:2312.10997, 2023.


---

## Figure file map (submission)

| Manuscript | File under `manuscript/figures/` |
|---|---|
| Figure 1 | `fig4_prompt_line.png` |
| Figure 2 | `fig5_esr_line.png` |
| Figure 3 | `fig6_methods_bars.png` |
| Figure 4 | `fig7_tradeoff_scatter.png` |
| Figure 5 | `fig8_vso_ablation.png` |
| Figure 6a | `fig9a_forest_prompt.png` |
| Figure 6b | `fig9b_forest_esr.png` |

## Author TODO before submission

- [ ] Affiliation, email, funding
- [ ] Target journal template + reference style
- [ ] Confirm Figure 5 caption (P2 ablation vs file name `fig8_vso_ablation`)

*Polished from v1.0 restructured DOCX; quantitative claims unchanged; no new experiments.*
