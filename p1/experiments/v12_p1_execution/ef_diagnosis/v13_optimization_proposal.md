# V1.3 Optimization Proposal (from E vs F diagnosis)

## 1. F vs E — real difference

**Only intended difference**: related non-target files → **Full (F)** vs **Digest (E)**.
Shared: EditTargets FULL, CandidateFull FULL, VP/vproof, must_full, Kmax=8, d=2, unrelated=NONE.

Runtime proof: RUR02 E = FILE hot + INDEX stable_*; F = all three FILE.

## 2. Where F is better

- Global ESR: F 35/72 vs E 32/72 (+4.2pp); bootstrap delta ESR (F-E)=0.0417 CI [0.0000,0.1250]
- Wins: F_only eps=4 vs E_only=1
- TPSE_F=1201.4 < TPSE_E=1303.4 (-7.8%)

## 3. Where F is worse

- TPAE_F=584.0 > TPAE_E=579.3 (0.8%) — **more tokens per attempted episode**
- TPSE improvement is largely **denominator effect**: F has more successes, so TPSE falls even though TPAE rises
- Full injection of related non-targets costs prompt tokens when those files are not needed

## 4. Why F may win (evidence vs hypothesis)

| Claim | Evidence |
| --- | --- |
| More complete related context reduces model confusion | **Partial**: F_only cases often have extra FILE blocks; not all cases show causal proof |
| Digest INDEX insufficient for 1.5B | **Hypothesis**: E RUR02 has INDEX only; still NO_EDIT on both — weak |
| TPSE drop from higher success rate | **Direct**: arithmetic on E/F totals |
| Not from looser safety | **Direct**: same ET/VP rules; et_verified all true both arms |

## 5. Can merge into E?

**Candidate A (data-backed)**: For must-adjacent related files — already shared via must_full.
**Candidate B (needs test)**: Upgrade related non-target Digest→Full when file is in dep graph of EditTargets (often already must).
**Candidate C**: Make F the default related=full — **TPAE +0.8%** must be accepted; not free.

**Do not**: drop VP/must/ET safety to gain speed (F did not do this).

## 6. V1.3 candidate (minimal)

1. **Related non-target default = Full** (adopt F policy) for 1.5B code-edit protocol.
2. Keep E as **Digest ablation arm** for papers.
3. Optional: auto-upgrade Digest→Full if related file in instruction or dep graph.
4. Keep VP, ET, CandidateFull unchanged.

## 7. Risk to VP safety
None if only changing non-target level; **must not** relax EditTargets/VP.

## 8. Minimal next experiment
- Prefer **descriptive merge analysis** on existing P1 before new runs.
- If new runs: small 8-task R=1 E vs F confirmation only.

## Classification
- **A (data)**: F has higher ESR, lower TPSE, higher TPAE on this P1; same safety flags.
- **B (hypothesis)**: Digest harms 1.5B more than Full costs.
- **C (do not)**: relax VP/ET to reduce tokens.

## Conclusion
F advantage is **context completeness for related non-targets**, paid with **~0.8% higher TPAE** and **~7.8% lower TPSE** (success denominator). Worth **V1.3 candidate default related=Full** with VP unchanged; validate small set before paper claim.
