# E vs F Arm Definition Diff

Generated: 2026-11-02T06:26:18.982856+00:00

## Sources
- preregistration: p1/docs/v1.2_experiment_preregistration.md (§3.0)
- config: p1/scripts/v12/config.py (_ARMS)
- runtime: runs/*/runner_out/.../context.txt

## E
{
  "non_target_related": "digest",
  "non_target_unrelated": "none",
  "code_in_config": true,
  "prereg_row": true,
  "runtime_example": "v1_RUR02_E_R1 step1: FILE hot + INDEX stable_*"
}

## F
{
  "non_target_related": "full",
  "non_target_unrelated": "none",
  "code_in_config": true,
  "prereg_row": true,
  "runtime_example": "v1_RUR02_F_R1 step1: FILE hot+stable_a+stable_b"
}

## Shared (must be identical)
{
  "must_full_edit_targets": "FULL both",
  "o_prime_vp": "same",
  "k_max": 8,
  "closure_depth": 2,
  "only_diff_per_prereg": "related non-target: Digest(E) vs Full(F)"
}

## Doc/code/runtime consistency
- E: config digest + prereg Digest/NONE/FULL + RUR02 INDEX files → **CONSISTENT**
- F: config full + prereg Full/NONE/FULL + RUR02 all FILE → **CONSISTENT**
- Single intended difference: related non-target level (Digest vs Full).

## Mechanism matrix

| Mechanism | E | F |
| --- | --- | --- |
| EditTargets → FULL | yes | yes |
| CandidateFull → FULL | yes | yes |
| VP/vproof omit | yes | yes |
| must_full | yes | yes |
| related non-target | DIGEST | FULL |
| unrelated non-target | NONE | NONE |
| Kmax / d | 8 / 2 | 8 / 2 |
| task_aware_r | on | on |
