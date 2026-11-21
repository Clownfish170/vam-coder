# VAM-Coder

**Verifiable context-management for multi-turn coding agents.**

VAM-Coder reduces redundant context transmission while checking that omitted workspace content remains **visible and version-consistent** at the final model-request boundary.

| Core mechanism | Role |
| --- | --- |
| **VP** (Visibility Proof) | Final-message visibility / hash check; reinject or fail closed |
| **F** (Selective Context Delivery) | Baseline selective delivery of related context |
| **S1** (Verified History Projection) | Fold redundant assistant `FILE` blocks by path (keeps first/last) |
| **S2** | Optional obligation-ledger heuristic (auxiliary only) |

**License:** MIT (`LICENSE`) · Third-party notices: `NOTICE`

---

## Repository layout

```text
vam-coder/
├── src/vam_coder/     # Product library (only production code entry)
├── tests/             # Unit tests for the product library
├── p1/scripts/        # Experiment harness (VP / S1 / S2 / runners)
├── p1/docs/           # Design & frozen preregistration documents
├── p1/tasks*/         # Self-designed evaluation task sets
├── docs/              # Architecture, glossary, history, reproducibility
│   └── history/       # Version evolution notes (V1.0 → V1.3E)
├── tools/             # Utility scripts
├── config/            # Default runtime config (config/default.json)
├── requirements.txt   # Pinned Python dependencies
├── LICENSE  NOTICE  CITATION.cff
└── README.md          # This file
```

**Not in this public tree** (kept on local disk only): experiment runs, raw logs, manifests, manuscript sources, and `p1/tasks_transfer_v1/` (embeds third-party library sources).

---

## Quick start

```bash
# Python >= 3.10 (tested 3.12.x)
pip install -r requirements.txt

# import smoke test (from repo root)
python -c "import sys; sys.path.insert(0, 'src'); import vam_coder; print('ok')"

# product unit tests
python -m pytest tests/ -q

# optional: P0 scenario self-check
python tools/run_p0_scenario.py
```

---

## Documentation

| Doc | Content |
| --- | --- |
| [docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md) | System overview |
| [docs/ARCHITECTURE_V13E.md](docs/ARCHITECTURE_V13E.md) | V13E flagship architecture |
| [docs/MECHANISM_VISIBILITY_PROOF.md](docs/MECHANISM_VISIBILITY_PROOF.md) | VP mechanism & boundaries |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | Terms (incl. O′ → VP) |
| [docs/DEVELOPMENT_HISTORY.md](docs/DEVELOPMENT_HISTORY.md) | Evolution V1.0 → V1.3E |
| [docs/history/](docs/history/README.md) | Per-version notes |
| [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) | How to rerun experiments |
| [docs/LIMITATIONS.md](docs/LIMITATIONS.md) | Claim boundaries |
| [p1/README.md](p1/README.md) | Experiment harness guide |

---

## Design task sets

Self-designed multi-step repository-editing tasks live under `p1/`:

- `p1/tasks/` — core task registry  
- `p1/tasks_p1_validation/` — 48-task confirmation suite  
- `p1/tasks_independent_v1*` — independent archetype suite  
- `p1/tasks_v13_holdout/` — holdout set  
- `p1/tasks_v13a_*`, `p1/tasks_v13d_chain/` — screening / chain variants  

Each task ships a small `project/` workspace, `eval/` tests, and `reference/` solutions.

> **Not included here:** `p1/tasks_transfer_v1/` (local only) — contains third-party library sources pending license review.

---

## Citation

See `CITATION.cff`. If you use this software, please cite the associated manuscript when published.

## Contributing

Issues and pull requests are welcome. Do not rewrite frozen experiment paths under local `p1/experiments/**`, and do not commit API keys or raw third-party datasets.
