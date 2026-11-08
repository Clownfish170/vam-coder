# RQ Gate Decision (prereg §6)

Point estimates use full P1 data. CI from task-cluster bootstrap B=10000, seed=20261102.

## Arm summary (ESR Wilson 95% CI)

| arm | success | ESR | Wilson95 | SPR | TPAE | TPSE | FETC_total | FETC_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 34/72 | 0.4722 | [0.361,0.586] | 0.6250 | 635.88 | 1346.5588 | 23496 | 618.3158 |
| B | 29/72 | 0.4028 | [0.297,0.518] | 0.5764 | 646.50 | 1605.1034 | 27316 | 635.2558 |
| D | 30/72 | 0.4167 | [0.310,0.532] | 0.5833 | 617.75 | 1482.6000 | 24933 | 593.6429 |
| E | 32/72 | 0.4444 | [0.335,0.559] | 0.5833 | 579.31 | 1303.4375 | 21696 | 542.4000 |
| F | 35/72 | 0.4861 | [0.374,0.599] | 0.6042 | 584.03 | 1201.4286 | 20229 | 546.7297 |
| G | 34/72 | 0.4722 | [0.361,0.586] | 0.6528 | 596.65 | 1263.5000 | 21932 | 577.1579 |
| H | 31/72 | 0.4306 | [0.323,0.546] | 0.5903 | 573.32 | 1331.5806 | 22136 | 539.9024 |

## Bootstrap Δ (E − ref), 95% percentile CI

| cmp | metric | point | CI_lo | CI_hi | valid | NA |
| --- | --- | --- | --- | --- | --- | --- |
| E-D | ESR | 0.0278 | -0.1111 | 0.1667 | 10000 | 0 |
| E-D | TPAE | -38.4444 | -62.4726 | -18.7222 | 10000 | 0 |
| E-D | TPSE | -179.1625 | -940.2685 | 328.5424 | 10000 | 0 |
| E-A | ESR | -0.0278 | -0.2361 | 0.1806 | 10000 | 0 |
| E-A | TPAE | -56.5694 | -85.8351 | -29.5139 | 10000 | 0 |
| E-A | TPSE | -43.1213 | -733.3895 | 755.4621 | 10000 | 0 |
| E-F | ESR | -0.0417 | -0.1250 | 0.0000 | 10000 | 0 |
| E-G | ESR | -0.0278 | -0.1389 | 0.0694 | 10000 | 0 |
| E-H | ESR | 0.0139 | -0.0417 | 0.0833 | 10000 | 0 |

## Gates (prereg §6.2)

| gate | point_pass | threshold | CI | evidence |
| --- | --- | --- | --- | --- |
| G1_ESR_E_vs_D | PASS | ΔESR >= -0.1 | [-0.1111,0.1667] | point_only |
| G2_ESR_E_vs_A | PASS | ΔESR >= -0.15 | [-0.2361,0.1806] | point_only |
| G3_TPSE_E_vs_D | PASS | ΔTPSE <= -74.13 | [-940.2685,328.5424] | point_only |
| G4_TPAE_E_vs_D | PASS | ΔTPAE <= 30.89 | [-62.4726,-18.7222] | point_and_ci |
| G5_E_vs_A_cost_claim | FAIL | TPSE<=0.95*A, TPAE<=1.05*A, ESR>=A-0.15 | [-733.3895,755.4621] | point_only |

## Interpretation discipline

- Point-estimate gates: **ALL CORE POINT GATES PASS**
- G1 CI lower bound >= -0.1: **NO / insufficient**
- If point passes but CI crosses -ε: phrase only as「点估计满足预注册门禁，把握度不足」——**不得**写 statistically non-inferior.
- cached_tokens is **not** used as KV cache savings evidence.
- Live VP/INSUFFICIENT block was **not** triggered in P0; do not claim live block verified.

## Failure summary (P1 steps)
- total failed steps: 401
- by category: {'MODEL_REASONING_ERROR': 256, 'MODEL_NO_EDIT': 96, 'CONTEXT_MISSING': 33, 'UNDETERMINED': 16}
- by arm: {'A': 54, 'B': 61, 'D': 60, 'E': 60, 'F': 57, 'G': 50, 'H': 59}
- top tasks: {'v1_DUP02': 42, 'v1_REN01': 42, 'v1_RUR03': 42, 'v1_DUP01': 40, 'v1_DEL02': 34, 'v1_SIG01': 30, 'v1_RUR02': 28, 'v1_CFD02': 21}
