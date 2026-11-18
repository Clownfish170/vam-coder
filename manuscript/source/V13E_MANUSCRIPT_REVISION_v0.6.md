# V13E Manuscript Revision v0.6 — with Experiment Data Visualizations

**Document type:** Full paper revision + mandatory data-visualization package  
**Baseline:** `论文草稿_v0.5_插图版.docx` (not overwritten)  
**Evidence freeze:** No new model runs; all numbers from on-disk experiment artifacts  
**Figure assets:** `v06_figs/fig4_*.png` … `fig9b_*.png` (generated from real data only)

---

## 0. Revision Scope and Honesty Rules Applied

This revision reorganizes the paper around two core mechanisms only:

| Kept as core | Demoted / removed from core claims |
|---|---|
| **VSO** — Visibility-Proof Selective Delivery (final-messages gate) | **S2** obligation ledger (auxiliary heuristic only) |
| **S1** — Verified History Projection (last complete `FILE` block per path; `first_last` in confirmatory runs) | **Dual Token** (negative result; appendix only) |
| Dual-model preregistered evaluation + fault injection + cluster sensitivity | CR/ICG as positive contributions; unfinished R5 as evidence |

**Visualization honesty rules enforced:**

1. No fabricated, interpolated, or CI-reconstructed raw task points for box/scatter “distribution” figures beyond what episode/task files contain.  
2. Task-level bootstrap CI ≠ archetype-cluster bootstrap CI (shown as separate series in Fig. 9).  
3. Episode count is never presented as independent *n*.  
4. TRUNC’s token advantage is shown (Fig. 6–7).  
5. PROJ’s ESR drop on DeepSeek is shown with error bars (Fig. 5, 9b).  
6. ESR CI crossing zero is never labeled “no difference at all” (Fig. 8b).  
7. Prompt savings are never described as latency / KV-cache savings.

---

## Abstract

Multi-turn coding agents resend growing workspace and history every step, inflating prompt cost and risking delivery of stale or incomplete state. We study **verifiable context reuse** via two mechanisms. **Visibility-Proof Selective Delivery (VSO)** checks at the *final* message list that in-scope omitted files remain fully visible with hashes matching the workspace; failures re-inject or fail closed. **Verified History Projection (S1)** keeps the last complete `FILE` block per normalized path (plus the first block under the confirmatory *first_last* dial), preserving the visible-file map VSO extracts. On preregistered DeepSeek-v4.1-flash-1017 and qwen3-coder-flash batches (56 tasks × 7 arms × 3 reps = 1176 episodes/model), projection cuts mean prompt tokens by **16.9%** (Δ = −632.6, 95% CI [−885.7, −403.5]) and **18.6%** (Δ = −697.3, CI [−969.7, −446.7]) versus the selective-delivery baseline F, while ESR stays within a −12pp non-inferiority margin (DeepSeek ΔESR = −1.2pp, CI [−5.4, +3.0]pp; Qwen +1.8pp, CI [−0.6, +5.4]pp). Controlled injection: VSO 30/30 phase-2 scenarios, unsafe ships = 0. Offline replay: 0 preservation violations / 2808 steps. Archetype-cluster bootstrap (32 clusters = 24 independent archetypes + 8 dose singletons) keeps all primary prompt CIs below zero and all ESR non-inferiority lower bounds ≥ −12pp. We claim neither universal safety nor KV/latency gains.

**Keywords:** multi-turn coding agents; visibility-proof delivery; context reuse; history projection; non-inferiority; fault injection

---

## 1 Introduction

Coding agents operate in a read–edit–verify loop. Each prompt concatenates system instructions, a trajectory that often contains full file rewrites, and workspace snapshots. Prompt growth is super-linear in trajectory length, and long-context degradation is documented in general and coding settings [1–5]. Truncation, summarization, retrieval, and memory systems reduce tokens—but *less context is not automatically safe context*. If a necessary file version never reaches the final request body, the task fails even when a “smart” memory layer believes state is retained.

This paper asks:

> How can multi-turn coding agents reduce redundant context transmission while verifying that selectively omitted or reused workspace content remains **visible and version-consistent** in the final model input?

We answer with two coupled mechanisms:

1. **VSO** — before each model call, extract full file bodies from the *final* messages, normalize paths, and require omitted (and edit-target/candidate) files to be present with disk-matching hashes; else re-expand or fail closed. VSO does **not** claim to discover all task-relevant information—only that objects *in check scope* satisfy visibility and version consistency at the delivery boundary.
2. **S1** — fold intermediate complete `FILE` blocks in assistant history by path, keeping the **last complete block per path** (and the first under `first_last`). Fold markers cannot re-match the extractor, so the path→body map used by VSO remains unchanged under the stated semantics (§3.5).

A rule-based obligation ledger (S2) appears only as an optional reminder heuristic and is **not** a contribution. Dual-token addressing failed its dedicated ablation and is excluded.

**Contributions**

1. **VSO:** a final-messages visibility and version gate for selective delivery, with fail-closed behavior under controlled delivery faults.  
2. **S1:** path-normalized history projection that preserves the VSO-visible file map under a constructive argument, with large-scale offline replay.  
3. **Evaluation:** preregistered multi-arm experiments on two LLMs, mechanism ablation, external truncation/summarization/retrieval baselines, controlled VSO fault injection, and post-hoc archetype-cluster sensitivity (Figures 4–9).

---

## 2 Related Work

### 2.1 Context compression and management

Token-level compressors (LLMLingua [14], Selective Context [15], lexical pipelines [16]) shrink general prompts. AGORA [17] shows token-level extractive compression can destroy agent action grammar and proposes step-granularity keep floors. ACON [ACON] optimizes long-horizon agent compression. Compact-Bench [Compact-Bench] measures damage from history replacement in coding agents; *Measure Before You Manage* [MBYM] evaluates heterogeneous working-memory objects; *Beyond Token Savings* [BTS] varies what/when/how much to compress. These reduce **volume** or improve **retention policy**; none of the verified sources installs a **hash-checked final-message gate** for every omission before the API call. VSO fills that delivery-boundary gap; it is not a new compressor.

### 2.2 Agent memory and retrieval

MemGPT [6], Generative Agents [7], Reflexion [8], Voyager [9], and surveys [10, 11] structure long-term/skill memory. TrawMem [12] and EvoMemBench [13] inform cost and non-inferiority framing. RAG [RAG1, RAG2] and ContextBench [22] focus on *what to fetch*, not whether the *final* prompt still contains omitted-but-required state.

### 2.3 Coding agents and repository context

SWE-bench [18], SWE-agent [19], AutoCodeRover [20], OpenHands [21] define interfaces and exploration. Full-file rewrites in multi-turn edits dominate history cost—exactly what S1 folds when delivery proofs still see the latest body.

### 2.4 Verification and safe context delivery

vCache [23] and prompt-cache auditing [24] verify *cache hits* for serving. PagedAttention [25] targets prefill efficiency. The verified combination of omission authorization against a visible-file map **plus** a pre-send check on the concrete final message list, with fail-closed re-injection, is the specific gap VSO addresses.

**Positioning:** compress/truncate (cost) · retrieve/remember (storage) · **VSO (final delivery verify)** · **S1 (project history safely relative to that verifier)**. We do not claim VSO is the first compressor or S1 the first history filter; novelty is the coupling, the final-messages check, and the closed-loop preregistered evaluation.

---

## 3 Method

### 3.1 Problem formulation

At step \(t\): workspace \(W_t\) (normalized path → body → SHA256); history \(H_t\); **final messages** \(\mathcal{M}_t\); omitted set \(\mathcal{O}_t\); edit targets \(E_t\); candidate-full \(C_t\).  
**Visible map** \(V(\mathcal{M})\): `full_files_in_messages` scans assistant `FILE:` fences and current-context `--- FILE … ---` blocks, assigning by normalized path with **later overwrite** (last-write-wins).  
**Complete `FILE` block:** path line + closed fence (not a truncated fragment).  
**Cost:** per-episode prompt tokens (including summarizer prompt tokens when applicable). **Capability:** ESR under a frozen step evaluator.

### 3.2 Overall architecture (implementation order)

1. History trim; optional **S1** (`project_history` on assistant `FILE` blocks).  
2. Optional **S2** open-obligation lines (auxiliary).  
3. **Phase A:** candidate proofs from *projected* history via the same extractor.  
4. Assemble \(\mathcal{M}_t\) (must / E / C / related policy).  
5. **Phase B (VSO):** `verify_omissions_in_messages`.  
6. Fail → force full rebuild → recheck → still fail → **no model call**.  
7. Gate → LLM API → apply `FILE` blocks to workspace.

S1 runs **before** proofs and assembly; VSO runs **after** assembly on the concrete \(\mathcal{M}_t\).

### 3.3 Visibility-Proof Selective Delivery (VSO)

**In scope:** paths the system identified as omitted or as E/C—not an open-ended “all task information” set.

**Checks on \(\mathcal{M}_t\):**  
- ∀ \(p\in\mathcal{O}_T\): \(p\in V(\mathcal{M}_t)\) and hash matches disk.  
- ∀ \(p\in E_t\cup C_t\): full file block in the **current** user context with disk hash (history-only visibility is insufficient).

**Failure:** re-inject (`force_full`), re-verify; persistent failure → `INSUFFICIENT` / fail-closed.  
**Limits:** not a proof of complete discovery; not semantic completeness of non-file text; not immune to check-to-HTTP races; controlled injection ≠ production fault rates.

```text
proofs ← full_files_in_messages(projected_history)          # Phase A
M_t ← assemble(history, policy, E, C)
V ← full_files_in_messages(M_t)                            # Phase B
for p in O_t: require p in V and SHA256(V[p]) == disk[p]
for p in E ∪ C: require full block in current context with disk hash
if fail: rebuild force_full; recheck; if fail: skip model call
else: allow model call
```

### 3.4 Verified History Projection (S1)

**Redundancy:** each edit step may restate whole files; intermediate versions remain in the transcript.  
**Why by path:** \(V\) is path-keyed last-write-wins; dropping *older complete* blocks while keeping the *last complete* block for each path cannot change \(V\). Length-based dropping can remove the last complete block and break proofs.  
**Retention:** last complete block per normalized path; under **`first_last`** (confirmatory), also the first complete block; others → fold marker without `FILE:` or fences. Non-assistant / non-`FILE` messages unchanged.  
**Relation to VSO:** Phase A and B share `full_files_in_messages`; see §3.5.  
**Cost:** one regex scan; no LLM.

### 3.5 Projection preservation argument (limited)

**Extractor \(V\):** sequential scan; later complete block for a path overwrites earlier.  
**Projection \(P\):** delete/replace every complete assistant `FILE` block except the last (and first, if `first_last`).

**Proposition.** If \(P\) retains, for every path, the last complete block occurring in \(H\), then \(V(P(H)) = V(H)\).

**Proof sketch.** \(V\) depends only on the last complete block per path in scan order; \(P\) preserves that block and only removes strictly earlier complete blocks for the same path; markers are outside the block grammar. ∎

**Scope:** constructive argument **relative to this extractor and retention rule**—not a theorem over arbitrary message languages. Empirically, 504 episodes / 2808 steps: **0** mismatches in \(V\) and pre-send fields; unit tests assert extractor equality. Finite replay ≠ formal proof. Discarded intermediate bodies are gone from the transcript even when the latest remains.

### 3.6 Complexity and limitations

S1 and VSO are linear in message characters / final size; hash cost per checked file. Limits: fence-form parsing only; no TOCTOU lock; file hash ≠ requirement satisfaction (why S2 is not claimed as completion detection).

---

## 4 Experimental Setup

### 4.1 Research questions

- **RQ1:** Does VSO-constrained delivery + S1 reduce prompt tokens vs F?  
- **RQ2:** Is ESR non-inferior (−12pp)?  
- **RQ3:** Does VSO detect controlled delivery faults and fall back without unsafe ships?  
- **RQ4:** Do directions hold across two models and under archetype-cluster resampling?

### 4.2 Models and tasks

| Item | Primary | Replication |
|---|---|---|
| Model | `deepseek-v4.1-flash-1017` | `qwen3-coder-flash` |
| Decode | T=0, seed=0, max_tokens=2048 | same |
| Tasks | 56 = 48 independent + 8 dose | same IDs |
| Structure | **24 archetypes × 2** + 8 dose singletons | same |
| Main arms | F, PROJ (F+S1), SAH (F+S1+S2 aux) × 3 = 1176 | 1176 |
| External | TRUNC (1300 char/step), SUMM (same-model; prompt cost included), RETR (BM25 top-3, keep latest) | same |

Reimplementations of external methods—not original author code. Primary metrics: prompt tokens/episode; ESR; NI margin **−12pp**.

### 4.3 Protocol and statistics

| Batch | Scale | Prereg | Role |
|---|---|---|---|
| P1 base | 720 | `088898a3` | F vs full / symbol-full |
| P2 ablation | 1680 | parent §6 | no-O′, redact, must |
| VSO | 31 + 30 | `0d9c292b` | fault injection |
| P3-A | 720 | `2ce8deff` | cross-model base |
| V13E | 1176×2 | `41526222` | PROJ/SAH vs F + externals |

**Confirmatory stats:** task-level paired means (episodes averaged within task×arm); bootstrap seed **20261102**, B=10000, cluster=task; sign-flip; Holm within pre-specified families; NI when 95% CI LB ≥ −12pp.  
**Post-hoc sensitivity (not preregistered):** archetype-cluster bootstrap B=5000; leave-one-archetype-out. **32 clusters = 24 independent archetypes + 8 dose singletons** (not 32 independent archetypes).

### 4.4 VSO fault-injection design

Phase 1: 31 deterministic scenarios (13 negative / 10 positive / 8 false-block controls) vs content-hash (B1) and ever-sent (B2) baselines. Phase 2: 10 frozen scenarios × 3 reps in a real runner (test-side monkeypatch). Metrics: UOR, SOR, FBR, FSR, EDR, exclusive detection on **V4**.

---

## 5 Results

### 5.1 Base selective delivery (P1)

F reduces prompt/episode by **23.6%** vs memory_off and **24.2%** vs symbol_full_read (Holm p=0.0002); ESR NI PASS (LB −4.2pp / −5.4pp). This frames the delivery stack; it is not an S1 result.

### 5.2 Mechanism attribution (P2) — Figure 8

Disabling the O′ omission/reuse path **increases** prompt by **+397.6 tokens/episode**, CI **[275.4, 524.8]** (Fig. 8a). The paired ESR difference F − no_O′ is **+0.42pp** with CI **[−2.08, +2.92]pp**, which **crosses zero**—we therefore report “no detectable ESR difference under this ablation,” **not** “ESR is identical.” Omission/reuse is the dominant cost lever in the baseline; S1 later attacks history redundancy on top of that machinery.

![Figure 8](v06_figs/fig8_vso_ablation.png)

**Figure 8.** P2 mechanism ablation (VSO/O′ omission path). **(a)** Prompt cost of disabling O′: +397.6 [275.4, 524.8] tokens/episode. **(b)** ESR difference F−no_O′ with 95% CI crossing 0.  
*Data:* `p1/experiments/p2_ablation/bootstrap_results.csv` (`vam_coder_v1.2_F−…_ablate_no_oprime`). *Unit:* task-paired mean of episode metrics. *n:* 48 P1 tasks × R5 structure as in P2 (paired task diffs). *CI:* task-cluster bootstrap 95%, seed 20261102, B=10000. *Status:* confirmatory mechanism family (effect sizes primary; Holm not applied to mechanism pairs per parent prereg).

### 5.3 VSO controlled fault injection

| Stage | Result |
|---|---|
| Phase 1 (31) | UOR=0, SOR=1.0, FBR=0, FSR=1.0; joint PASS |
| EDR V1–V5 | VSO 1.0 · B1 0.0 · B2 0.8; **exclusive VSO = 1 (V4)** |
| Phase 2 (30) | 30/30 correct; **unsafe_ship=0; DHO=0** |

V4: content hash exists and was once sent, but the block is absent from the final messages—B1/B2 authorize; VSO blocks. **Limit:** controlled injections only.

### 5.4 Main confirmatory arms — Figures 4–5

Episode-level arm means (n=168/arm/model) match the analysis verdict tables:

| Arm | DS ESR | DS prompt | QW ESR | QW prompt |
|---|---:|---:|---:|---:|
| F | 0.649 | 3747.5 | 0.512 | 3740.2 |
| PROJ | 0.595 | 3068.9 | 0.536 | 3055.2 |
| SAH | 0.637 | 3114.9 | 0.530 | 3042.9 |

**Figure 4 — Prompt tokens (F → PROJ → SAH).** Both models show large drops from F to PROJ/SAH. DeepSeek: PROJ−F task mean **−678.7** [−960.7, −431.2]; SAH−F **−632.6** [−885.7, −403.5] (−16.9% of F). Qwen: **−685.0** [−949.4, −442.3]; **−697.3** [−969.7, −446.7] (−18.6%). Error bars are **task-level** bootstrap CIs on task means (not episode *n*).

![Figure 4](v06_figs/fig4_prompt_line.png)

**Figure 4 caption.** Prompt tokens per episode across configurations. Points: task-level means; whiskers: 95% task-cluster bootstrap CI (seed 20261102, B=10000). Panels (a) DeepSeek and (b) Qwen are **not** pooled. *Sources:* `…/v13e_ds_20261111_160133/episode_metrics.csv`, `…/v13e_qwen_20261112_182237/episode_metrics.csv`, CIs aligned with `analysis_verdict.json` H-E1/H-E4a. *Confirmatory.*

**Figure 5 — ESR (honest trade-off).** DeepSeek PROJ ESR **falls** vs F (task mean 0.595 vs 0.649; paired ΔESR **−5.4pp**, CI [−10.1, −1.2]pp)—non-inferior at −12pp but **not** free. SAH on DeepSeek is closer to F (Δ **−1.2pp**, CI [−5.4, +3.0]pp). Qwen PROJ/SAH are slightly **above** F on point estimates; all NI tests PASS. Y-axes are not truncated to exaggerate gaps; CI whiskers are shown.

![Figure 5](v06_figs/fig5_esr_line.png)

**Figure 5 caption.** Episode success rate (%) with task-level 95% bootstrap CIs. Same data and unit as Figure 4. PROJ−F and SAH−F differences are annotated; SAH savings are **not** attributed to S2. *Confirmatory* (H-E2, H-E4b).

### 5.5 External baselines — Figures 6–7

![Figure 6](v06_figs/fig6_methods_bars.png)

**Figure 6 caption.** Prompt tokens by method (episode means; whiskers = task bootstrap 95% CI). Percent labels are **relative to F** on the same model. **TRUNC is cheapest on pure prompt** (DS 2456, QW 2347) by discarding oldest history without a delivery proof. **SUMM is most expensive** once summarizer prompt cost is included (DS 5006.5 = +33.6% vs F; aux column separately 1724.2 = summarizer prompt+completion—not added again to the bar). RETR intermediate. SAH is **not** the minimum-token method; the figure does not imply global superiority. *Sources:* arm_summary / analysis_verdict arm_table. *Confirmatory same-batch.*

![Figure 7](v06_figs/fig7_tradeoff_scatter.png)

**Figure 7 caption.** Efficiency–capability plane: x = prompt tokens/episode (lower better), y = ESR % (higher better); episode means with task-bootstrap error bars where available. Filled markers = core arms; open markers = external baselines; circles = DeepSeek, squares = Qwen. **Reading:** TRUNC occupies low-cost / mid-ESR; SUMM high-cost; PROJ moves left with ESR cost on DeepSeek; SAH moves left while staying near F ESR. No causal claim beyond same-batch randomized arm assignment under one protocol.

**Paired verdicts (task-level, n=56):**

| Pair | DS mean [95% CI] | QW mean [95% CI] |
|---|---|---|
| SAH−F prompt | −632.6 [−885.7, −403.5] | −697.3 [−969.7, −446.7] |
| SAH−F ESR | −0.012 [−0.054, +0.030] | +0.018 [−0.006, +0.054] |
| PROJ−F prompt | −678.7 [−960.7, −431.2] | −685.0 [−949.4, −442.3] |
| PROJ−F ESR | −0.054 [−0.101, −0.012] | +0.024 [−0.006, +0.060] |
| SAH−TRUNC ESR | +0.006 [−0.018, +0.030] | 0.000 [−0.036, +0.036] |
| SAH−SUMM prompt | −1891.6 [−2575.7, −1261.1] | −1205.9 [−1595.9, −832.5] |
| SAH−RETR prompt (desc.) | −153.6 [−251.6, −58.7] | −133.0 [−220.5, −48.5] |

All primary efficiency CIs exclude 0; all primary ESR NI bounds ≥ −12pp. `GATE_ALL=PASS` both models.

### 5.6 Statistical robustness — Figure 9

Post-hoc archetype-cluster bootstrap (B=5000) and leave-one-archetype-out (32 LOO runs) on the same paired task differences:

![Figure 9a](v06_figs/fig9a_forest_prompt.png)

**Figure 9a caption.** Prompt-token differences PROJ−F and SAH−F. **Solid:** task-level paired bootstrap 95% CI (**confirmatory**, seed 20261102, B=10000). **Dashed:** archetype **cluster** bootstrap 95% CI (**sensitivity**, B=5000; **32 clusters = 24 independent archetypes + 8 dose singletons**). **Gray bar:** leave-one-archetype-out mean range (**sensitivity**). Zero line = no difference. All cluster CIs remain strictly &lt; 0. Task CIs are ~1.34–1.39× narrower than cluster CIs—task bootstrap is somewhat optimistic for prompt.

![Figure 9b](v06_figs/fig9b_forest_esr.png)

**Figure 9b caption.** ESR differences in **percentage points** with **non-inferiority margin −12pp** (dotted). Same three series as 9a. All task and cluster lower bounds are ≥ −12pp; LOO means never cross the margin. DS PROJ−F is the tightest (task LB ≈ −10.1pp; cluster LB ≈ −9.6pp). **Sensitivity only—not a replacement for preregistered tests.** LOO ESR CI lower bounds also remained ≥ −12pp in the offline audit (`V13E_CLUSTER_ROBUSTNESS_AUDIT.md`).

### 5.7 Supporting disclosures

- S1 replay: 504 episodes / 2808 steps, 0 extractor/pre-send mismatches (`replay_report.json`).  
- Dual-token: 960 episodes; independent contribution **not** supported (Holm p≈0.109; frozen NI fail; control lacked VSO). Not a contribution.  
- CR/ICG: ≈−1.4% prompt, CI includes 0 → no claimed gain.  
- Protocol: 51/51 EMPTY_TRUNC attribution; isolated 4096 retest resolved 44/51 (86.3%) without touching frozen data.  
- Unfinished independent R5 (24/720): **not** evidence.

---

## 6 Discussion

**Supported:** Under the frozen protocol, verifiable selective delivery + path-based history projection reduces prompt tokens ~17–19% vs the same stack without projection, with ESR non-inferior at −12pp on two models. VSO’s added value vs naive hash/cache checks is demonstrated on V4-class faults. S1’s preservation property matches shared-extractor design and replay.

**Not supported:** universal safety; formal S1 verification for all inputs; S2 as correct completion detection or as the source of SAH savings; dual-token gains; KV/latency/memory savings; ESR *superiority* of PROJ; generalization beyond the tested synthetic micro-repos and two models.

**Limitations:** synthetic tasks; two model families; archetype correlation (Fig. 9); non-bit-determinism at T=0; TOCTOU window; optional S2 heuristics; reimplemented external baselines.

**Practice:** If you need proof that omitted files are still in the request, use a VSO-style final gate. If history is dominated by repeated full-file rewrites, apply S1 **before** proof extraction so savings and verification share one map. Do not replace delivery checks with summarization when total cost includes the summarizer.

---

## 7 Conclusion

We presented **verifiable context reuse** as VSO (final-messages visibility/version gate) plus S1 (path projection of complete history `FILE` blocks). Preregistered DeepSeek and Qwen experiments show **16.9%** and **18.6%** prompt reductions with ESR within −12pp; controlled injections show VSO with zero unsafe ships in phase 2; replay shows no preservation violations; archetype-cluster resampling does not reverse primary conclusions (Fig. 9). Scope is deliberate: delivery verification under controlled faults; constructive preservation under a specified extractor; prompt-token savings only. Frozen confirmatory batches need no reopening for this paper.

---

## 8 Figure–text integration map

| Figure | Section | Argument it supports |
|---|---|---|
| **Fig. 4** | §5.4 | RQ1: S1 configs cut prompt tokens on both models |
| **Fig. 5** | §5.4 | RQ2: ESR trade-off; PROJ drop on DS is real; SAH near F |
| **Fig. 6** | §5.5 | External methods; TRUNC cheapest; SUMM costly with aux; SAH not min-token |
| **Fig. 7** | §5.5 | Efficiency–capability plane for discussion |
| **Fig. 8** | §5.2 | VSO/O′ ablation: +397.6 prompt; ESR CI crosses 0 |
| **Fig. 9a–b** | §5.6 | Confirmatory vs cluster/LOO robustness; NI margin |

In-text citations: “As shown in Figure 4…”, “Figure 5 makes the PROJ ESR cost explicit…”, “Figure 6 preserves TRUNC’s token advantage…”, “Figure 8a quantifies the O′ ablation at +397.6 [275.4, 524.8]…”, “Figure 9 separates confirmatory task CIs from post-hoc cluster CIs…”.

---

## 9 Data provenance matrix (mandatory)

| Fig. | Primary files | Fields | n (unit) | Point estimate | Error bar | CI | Confirmatory? |
|---|---|---|---|---|---|---|---|
| 4 | `episode_metrics.csv` (DS/QW runs) | `prompt_sum`, `task_id`, `arm_label`, `rep` | 56 tasks × 3 reps/arm (task means); 168 eps/arm | task mean of within-task episode means | 95% CI | task bootstrap B=10000 seed 20261102 | **Yes** |
| 5 | same | `eval_success` | same | task mean ESR | 95% CI | same | **Yes** (H-E2/E4b) |
| 6 | same + `analysis_verdict.json` arm_table | `prompt_sum` | 168 eps/arm (bars); CI from task means | episode mean (bar), task CI (whisker) | 95% CI | task bootstrap | **Yes** same-batch |
| 7 | same | `prompt_sum`, `eval_success` | 168 eps/arm | episode mean | task CI in x/y | task bootstrap | **Yes** same-batch |
| 8 | `p2_ablation/bootstrap_results.csv` | paired Δ prompt & ESR for no_oprime | paired tasks in P2 | Δ mean | 95% CI | task bootstrap | **Yes** mechanism family |
| 9 | `episode_metrics` recompute + cluster audit | paired task diffs | 56 tasks; 32 clusters | mean / cluster mean | task CI + cluster CI + LOO range | task B=10000; cluster B=5000 | Task=**Yes**; cluster/LOO=**No (sensitivity)** |

**Not used:** any synthetic task-level draws, CI reverse-engineered boxplots, or mixed task/cluster CI as one series.

---

## Appendix A. Reproducible plotting code (reference)

Run from a Python with `matplotlib` and `numpy` (e.g. project env used for figures). Inputs must already exist—**do not regenerate experiment data**.

```python
# Skeleton: loads real CSVs / verdict JSON, writes v06_figs/fig*.png
# Full executed script: C:\\Users\\Xu176\\AppData\\Local\\Temp\\make_figs.py
# Data snapshot used: v13e_fig_data.json (episode_metrics + verdict + cluster audit)

import csv, json, random
from pathlib import Path
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(r"D:\\Demo\\DynaMem\\vam-coder")
SEED, B, B_CL = 20261102, 10000, 5000
F, PROJ, SAH = "vam_coder_v1.2_F", "vam_coder_v1.3E_PROJ", "vam_coder_v1.3E_SAH"

def load(run):
    rows = list(csv.DictReader(open(Path(run)/"episode_metrics.csv", encoding="utf-8-sig")))
    return [r for r in rows if r.get("status") == "OK"]

def task_pairs(rows, new, base, metric):
    acc = defaultdict(lambda: defaultdict(list))
    for r in rows:
        acc[r["task_id"]][r["arm_label"]].append(float(r[metric]))
    diffs = []
    for t in sorted(acc):
        if new in acc[t] and base in acc[t]:
            a = sum(acc[t][new])/len(acc[t][new])
            b = sum(acc[t][base])/len(acc[t][base])
            diffs.append(a - b)
    return diffs

def boot_ci(vals, seed=SEED, B=B):
    rng = random.Random(seed)
    n = len(vals)
    stats = [sum(vals[rng.randrange(n)] for _ in range(n))/n for _ in range(B)]
    stats.sort()
    return sum(vals)/n, stats[int(0.025*B)], stats[min(B-1, int(0.975*B))]

# Fig 4/5: line plots of task means ± CI for F,PROJ,SAH × {DS,QW}
# Fig 6: bar chart of six methods × two models, % vs F
# Fig 7: scatter prompt vs ESR, marker by model, fill by core/external
# Fig 8: horizontal bars for (no_O'-F) prompt and (F-no_O') ESR from p2 bootstrap_results.csv
# Fig 9: forest of task CI / cluster CI / LOO range for PROJ-F & SAH-F × {prompt, esr}
# Cluster bootstrap: resample 32 clusters (24 family + 8 dose::*) with replacement, B=5000
```

**Cluster definition used in Fig. 9:**  
`family` from `p1/tasks_independent_v1/independent_tasks.json` (24 values × 2 tasks); dose tasks `dose_D01`…`dose_D08` as singleton clusters `dose::*`. Total **32** clusters—not 32 archetypes.

---

## Appendix B. Negative and boundary results (must remain visible)

1. **PROJ ESR (DeepSeek):** −5.4pp, CI [−10.1, −1.2]pp → NI PASS only; not “no effect.”  
2. **TRUNC:** lowest prompt cost among compared arms; SAH does not dominate on tokens.  
3. **SUMM:** total prompt higher than F after including summarizer prompt cost.  
4. **P2 ESR ablation:** CI crosses 0 → “no detectable difference,” not “identical.”  
5. **Dual token:** no independent contribution.  
6. **S2:** not a core innovation; SAH−F ≠ S2 effect.  
7. **Cluster CIs wider than task CIs** for prompt—disclose; do not present only the narrower confirmatory interval as if it were the full uncertainty story.

---

## Appendix C. References

[1–25] as in manuscript v0.6 (Lost in the Middle; RULER; LongBench; context rot; MemGPT; Generative Agents; Reflexion; Voyager; memory surveys; TrawMem; EvoMemBench; LLMLingua; Selective Context; lexical compression; AGORA; SWE-bench; SWE-agent; AutoCodeRover; OpenHands; ContextBench; vCache; cache audit; PagedAttention; RAG).

**Verified near-work (arXiv, 2026-11-13):**  
[ACON] arXiv:2510.00615 (comment: ICML 2026) · [Compact-Bench] arXiv:2610.31710 · [MBYM] arXiv:2608.31057 · [BTS] arXiv:2609.32961 · [FOCUS] arXiv:2609.37590 · [AGORA] arXiv:2605.26596.

**Not cited (no primary source found on search date):** CompactionBench/APEC; “Context Compression for LLM Agents Survey (EMNLP 2026)”; “Agentic Memory Should Localize Compression.”

---

## Appendix D. Pre-submission check (this revision)

| Check | Status |
|---|---|
| All Fig. 4–9 numbers from disk artifacts | **Yes** |
| Figure/text numeric consistency | **Yes** (tables ↔ verdict ↔ figs) |
| Task vs cluster CI not merged | **Yes** (Fig. 9 separate series) |
| Episode *n* not sold as independent sample | **Yes** (captions state task unit for CIs) |
| TRUNC advantage visible | **Yes** (Fig. 6–7) |
| PROJ ESR drop visible | **Yes** (Fig. 5, 9b) |
| P2 ESR “CI crosses 0” not overclaimed | **Yes** (Fig. 8b) |
| Sensitivity ≠ confirmatory | **Yes** (Fig. 9 captions) |
| No prompt→latency/KV claim | **Yes** |
| v0.5 not overwritten | **Yes** |
| Single deliverable this task | **`V13E_MANUSCRIPT_REVISION_v0.6.md`** |

---

*End of V13E_MANUSCRIPT_REVISION_v0.6.md.*
