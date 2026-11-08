# P1 Data Integrity Report

Generated: 2026-11-02T06:09:29.207564+00:00

## Coverage
- steps: 1008 (expect 1008)
- episodes: 504 (expect 504)
- tasks: 24 (expect 24)
- arms: ['A', 'B', 'D', 'E', 'F', 'G', 'H']
- reps: [1, 2, 3]
- all 2 steps: True
- missing matrix cells: []
- extra cells: []
- duplicate episode+step: 0
- eval NA: 0
- prompt>0: 1008

## Randomization
- rand n/unique: 504/504
- episodes match rand order set: True

## Workspace
- pre/post/diff: 504/504/504

## Notes
- A/B stdout GBK decode warnings during run: recorded as harness I/O issue, not experiment failure (returncode 0, 144 steps each present).
- Raw data not modified.

## Input SHA256
- per_step_all: `c2c5a887ccfa996cc22cec19a4efdc58dbe8b2e0ca8469f125e9f09224ae01ee` (`p1\experiments\v12_p1_execution\per_step_all.csv`)
- summary_by_arm: `c308ff067b856039b9536d30274eef5f86a64d4b3cec646460c2656ee20d6e7c` (`p1\experiments\v12_p1_execution\summary_by_arm.csv`)
- randomization: `145f569b51b889db39c66635c8f7be16387ea7bbdf108043d7d3f7177da24bd0` (`p1\experiments\v12_p1_execution\randomization_manifest.json`)
- execution_summary: `6ea32ea6c0e17f6e33c3e0ce37552317ba84582e3bacf9efe9c7cde989c8b6af` (`p1\experiments\v12_p1_execution\execution_summary.json`)
- prereg: `7d594e1c2b5de063ef75c2bdbaa65e5365607c1651a873b2960fc9b70a7425fc` (`p1\docs\v1.2_experiment_preregistration.md`)
