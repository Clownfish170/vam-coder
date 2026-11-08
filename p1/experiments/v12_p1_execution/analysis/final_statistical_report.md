# P1 Final Statistical Report (V1.2-r2.2)

Read-only analysis. Seed=20261102, bootstrap B=10000, task-cluster (all R kept per sampled task).

## Integrity
See data_integrity_report.md. episodes=504, steps=1008, ws=504/504/504.

## Primary metrics

- **A**: ESR 34/72 = 0.472 (Wilson [0.361,0.586]); SPR 90/144; TPAE 635.9; TPSE 1346.5588; FETC_total 23496; FETC_mean 618.3158
- **B**: ESR 29/72 = 0.403 (Wilson [0.297,0.518]); SPR 83/144; TPAE 646.5; TPSE 1605.1034; FETC_total 27316; FETC_mean 635.2558
- **D**: ESR 30/72 = 0.417 (Wilson [0.310,0.532]); SPR 84/144; TPAE 617.8; TPSE 1482.6000; FETC_total 24933; FETC_mean 593.6429
- **E**: ESR 32/72 = 0.444 (Wilson [0.335,0.559]); SPR 84/144; TPAE 579.3; TPSE 1303.4375; FETC_total 21696; FETC_mean 542.4000
- **F**: ESR 35/72 = 0.486 (Wilson [0.374,0.599]); SPR 87/144; TPAE 584.0; TPSE 1201.4286; FETC_total 20229; FETC_mean 546.7297
- **G**: ESR 34/72 = 0.472 (Wilson [0.361,0.586]); SPR 94/144; TPAE 596.7; TPSE 1263.5000; FETC_total 21932; FETC_mean 577.1579
- **H**: ESR 31/72 = 0.431 (Wilson [0.323,0.546]); SPR 85/144; TPAE 573.3; TPSE 1331.5806; FETC_total 22136; FETC_mean 539.9024

## RQ answers (paper-level, cautious)

- **RQ1**: Point gates G1–G4: G1=PASS, G2=PASS, G3=PASS, G4=PASS. CI for ΔESR(E−D) [-0.1111,0.1667]. 点估计满足门禁但若 CI 跨过非劣界，仅可写点估计门禁 + 把握度不足。 **不得**写成已证非劣。
- **RQ2**: Task-aware assembly (E vs F/G/H) — see bootstrap ESR deltas; interpret descriptively with CI width.
- **RQ3**: VP/vproof — P1 runner uses pre_send checks; live INSUFFICIENT block not observed in P0/P1 runs; unit/mock only for block path. VP does not prove semantic equivalence.
- **RQ4**: Suitable for paper **draft** with limitations; not for claims of architectural validity or large-model generalization; related-work novelty not systematically verified.

## Failure attribution

- Categories: {'MODEL_REASONING_ERROR': 256, 'MODEL_NO_EDIT': 96, 'CONTEXT_MISSING': 33, 'UNDETERMINED': 16}
- By arm: {'A': 54, 'B': 61, 'D': 60, 'E': 60, 'F': 57, 'G': 50, 'H': 59}
- Detail: failure_attribution.csv

## Reproducibility

- script: analysis/_run_analysis.py
- seed=20261102, B=10000
