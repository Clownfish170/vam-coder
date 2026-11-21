# Open-Source Pre-Release Checklist — VAM-Coder

**Status:** working checklist (not a legal opinion)  
**Date:** 2026-11-21  
**Repo license:** MIT (`LICENSE`) — **code only** until third-party/data review completes  
**Rule:** Any row marked **NEEDS REVIEW** must be confirmed against the official license text / dataset card / vendor ToS **before** public release. Do not assume compatibility.

---

## 0. Go / No-Go summary

| Gate | Status |
|------|--------|
| Own code LICENSE (MIT) | **READY** |
| Dependency licenses documented | **NEEDS REVIEW** (table §1) |
| Dataset / benchmark redistribution | **NEEDS REVIEW** (table §2) |
| Model / API terms | **NEEDS REVIEW** (table §3) |
| Secrets / credentials in tree | **PASS (spot-check)** — env-var API keys; re-scan before publish |
| Personal data / absolute paths | **NEEDS REVIEW** (§4) |
| Repo size / history hygiene | **NEEDS REVIEW** (~8k+ tracked `p1/` files; loose objects large) |
| README / install / cite | **PARTIAL** — MIT + CITATION present; install path for full experiments incomplete |
| Public GitHub/Gitee | **NOT READY** until §1–§4 closed or scope reduced (§5) |

**Recommendation:** Publish in phases (§5). Do **not** push a full public dump of all experiment runs until §1–§4 are signed off.

---

## 1. Third-party dependency license table

Source of truth for versions: `requirements.txt` (pinned). Verify each row on PyPI (or upstream repo) **at release time**.

| Package | Pinned version | Declared license (verify) | Compatible with MIT? | Redistribution in this repo? | Action |
|---------|----------------|---------------------------|----------------------|------------------------------|--------|
| tree-sitter | 0.26.0 | **MIT** (PyPI classifier, checked 2026-11-21) | Yes | Not vendored (pip dep) | Listed in `NOTICE` |
| tree-sitter-python | 0.25.0 | **MIT** (PyPI license field, checked 2026-11-21) | Yes | Not vendored | Listed in `NOTICE` |
| blake3 | 1.0.11 | **CC0-1.0 OR Apache-2.0** (PyPI license field, checked 2026-11-21) | Yes (either) | Not vendored | Listed in `NOTICE` |
| pytest | 9.1.1 | **MIT** (PyPI license_expression, checked 2026-11-21) | Yes | Not vendored | Listed in `NOTICE` |
| Python stdlib / runtime | ≥3.10 (3.12.x used) | PSF-2.0 (typical) | Yes | N/A | Note in README |
| Docker Engine / Desktop (used only for transfer eval) | host-dependent | **NEEDS REVIEW** (Docker ToS; not redistributed) | N/A if not shipped | **Do not** redistribute Docker | State “optional for transfer experiments” |
| WSL2 (was used for Docker backend) | system | Microsoft terms | N/A | Not redistributed | Already removed on this machine; document as optional |

**Vendored code check**

| Item | Path | License | Action |
|------|------|---------|--------|
| Product package | `src/vam_coder/` | Covered by repo MIT | OK if no third-party code copied in — **spot-review imports** |
| Experiment harness | `p1/scripts/` | Covered by repo MIT if original | Confirm no copied GPL/AGPL snippets |
| Local reimplementation baselines (TRUNC/SUMM/RETR) | experiment code | Original to this repo | State clearly they are **not** upstream official code |
| `archive/*.zip` / `*.bundle` | large blobs | **NEEDS REVIEW** | Prefer **exclude from git** (already partly gitignored); ship separately if needed |

**NOTICE file (recommended before publish):** list MIT own code + each dependency name/version/license once §1 is filled.

---

## 2. Datasets, benchmarks, and task assets

| Asset | Where it appears | Upstream license (verify) | Redistribute here? | Action |
|-------|------------------|---------------------------|--------------------|--------|
| **SWE-bench Lite** instances (10 used) | `p1/experiments/v13e_p1_swebench/` (tasks JSON, logs, patches context) | **NEEDS REVIEW** — check SWE-bench repo + Hugging Face dataset card for test-split terms | Only if card allows; else ship **IDs + instructions to download**, not raw dumps | Prefer **download script + instance IDs** over committing full dataset text |
| SWE-bench task prompts / repo snapshots in run logs | `episodes/**/prompt.txt`, `context.txt`, `workspace/**` | May embed third-party repo source (e.g. requests, flask, pytest, pylint) under **their** licenses (MIT/Apache/BSD/PSF…) | Risky as a bulk public dump | **NEEDS REVIEW**; consider redacting or restricting to derived metrics |
| Synthetic micro-repository tasks (main study) | `p1/tasks*`, `p1/experiments/**` | Created for this project → repo MIT (if original) | Yes if no third-party code inside | Spot-check task `project/` files for copied upstream code |
| Preregistration / freeze JSON | `p1/docs/*`, `prereg_freeze.json` | Own work → MIT | Yes | Keep as-is |
| Analysis CSVs / bootstrap outputs | experiment dirs | Own derived data | Yes (preferred public payload) | Safe to publish with methods |
| `randomization_manifest.json` etc. | experiment dirs | Own | Yes | OK |

**Minimum safe data release (recommended):**

1. Source code (`src/`, `p1/scripts/` if desired)  
2. Synthetic tasks + manifests  
3. Preregistrations + analysis scripts + summary CSVs/JSON  
4. **SWE-bench:** instance IDs + protocol + `PROTOCOL.md`; raw episode dumps **optional / gated**

---

## 3. Models, APIs, and third-party services

| Service | Used for | Terms risk | Action |
|---------|----------|------------|--------|
| DeepSeek API (`deepseek-v4.1-flash-1017` etc.) | Confirmatory + transfer runs | Commercial ToS; output ownership; **no keys in repo** | Document model IDs; never commit `VAM_API_KEY` / `OPENAI_API_KEY` |
| Qwen / token-plan endpoint (`qwen3-coder-flash`, `qwen3.8-flash`) | Confirmatory + transfer | Same class of risk | Same |
| OpenAI-compatible MaaS wrapper | harness | Vendor-specific | Describe as “OpenAI-compatible endpoint” without leaking base URL secrets |
| Hugging Face (dataset download path, if any) | SWE-bench Lite fetch | Dataset card terms | Prefer official download instructions |

**Credential scan (pre-publish) — executed 2026-11-21:**

- [x] Tracked-file scan for `sk-…`, `ghp_…`, `AKIA…`, private-key PEM blocks: **0 hits** in product/docs scope  
- [x] Source/docs/scripts deep scan (`.py/.md/.json/...`): **0 hits** of real key material  
- [x] API usage is **environment variables only** (`VAM_API_KEY` / `OPENAI_API_KEY` via `os.environ`) — docs mention the *names*, not values  
- [x] No `.env` / `*.pem` / `id_rsa*` / credential files tracked in git  
- [x] Benchmark episode text may contain *example* passwords/Bearer strings from third-party repos — noise, not your keys; still avoid bulk-publishing raw episode dumps  
- [ ] **Before public push:** re-run scan on the exact tree you will publish; never commit `.env` or real keys  
- [ ] If a key was ever pasted into chat/logs outside the repo: **rotate it**

---

## 4. Privacy, paths, and non-public material

| Item | Finding | Action |
|------|---------|--------|
| Absolute paths `D:\Demo\...` | Present inside frozen run logs / eval outputs | **NEEDS REVIEW** before full public dump; OK if you publish code+summaries only |
| Email in manuscript | `Xu1764602693@hotmail.com` | Intentional for paper; decide if git history should expose it (paper will) |
| Local hostnames / usernames in logs | Possible (`Xu176` in paths) | Redact or exclude raw logs from public zip |
| `llama.cpp` / `models/` (workspace outside repo) | Not in `vam-coder` git | Do not publish model weights without license |
| Backup archives | `V13E_PROJECT_ARCHIVE.zip` in `archive/` | **Exclude from git** (already ignored); do not auto-publish |
| Startup leftover VBS | `archive/startup-leftovers/` | Harmless script; optional to strip before public |

---

## 5. Release scope options (pick one)

| Option | Contents | Risk | When |
|--------|----------|------|------|
| **A. Code + methods only (safest)** | `src/`, `p1/scripts/`, docs, synthetic tasks, prereg, analysis code + summary tables | Low | Can go public first |
| **B. Code + full synthetic experiments** | A + all `p1/tasks*` + non-SWE-bench experiment outputs | Medium (path/log hygiene) | After §4 path scrub |
| **C. Full experimental dump** | B + all SWE-bench episode logs/workspaces | **High** (third-party code in workspaces) | Only after §2 sign-off |
| **D. Private then public** | Push **private** remote; review GitHub UI; then flip public | Controlled | **Recommended process** |

**Suggested path:** D → A public now → B after path scrub → C only if license review clears.

---

## 6. Documentation completeness (publish pack)

| Artifact | Status |
|----------|--------|
| `LICENSE` (MIT) | **DONE** |
| `README` install for `src/` | **PARTIAL** — add `pip install -r requirements.txt` + import smoke test |
| Repro doc | `docs/REPRODUCIBILITY.md` **DONE** (link from README) |
| `CITATION.cff` | **DONE** (verify author formatting for GitHub) |
| `CONTRIBUTING.md` | **DONE** |
| `CHANGELOG.md` | **DONE** |
| `NOTICE` (third-party) | **DONE** (`NOTICE` — deps verified from PyPI 2026-11-21) |
| Dataset download instructions for SWE-bench | **TODO** if Option C |
| Security contact / vulnerability policy | **TODO** (optional for Q4 code release) |

---

## 7. Pre-publish command checklist

```text
[ ] Fill §1 licenses from PyPI/official LICENSE files; write NOTICE
[ ] Decide release Option A/B/C (§5)
[ ] If B/C: scrub or exclude absolute paths & raw episode workspaces
[ ] Full secret scan on tracked files only
[ ] Remove or ignore: archive/*.zip, *.bundle, server logs, startup-leftovers (optional)
[ ] Confirm .gitignore does not drop required tracked files
[ ] Private remote push → visual review of GitHub file tree
[ ] Tag e.g. v1.0.0-rc1 with date + paper manuscript pointer
[ ] Flip public; enable GitHub citations if desired
[ ] After paper acceptance: update CITATION.cff with DOI/journal
```

---

## 8. Explicit non-actions (until review done)

- Do **not** relicense third-party code as MIT.  
- Do **not** claim official SWE-bench or official baseline implementations.  
- Do **not** publish API keys or full vendor base URLs with secrets.  
- Do **not** attach model weights (`models/`) without separate license review.  
- Do **not** treat this checklist as legal advice.

---

## 9. Owner sign-off

| Block | Owner | Date | Initial |
|-------|-------|------|---------|
| §1 Dependency licenses | 2026-11-21 PyPI check + `NOTICE` written | **DONE** (deps) |
| §2 Dataset redistribution | | | |
| §3 Model/API ToS | | | |
| §4 Privacy/paths | | | |
| §5 Release option chosen | | | |
| Public push authorized | | | |

*End of checklist. License rows marked NEEDS REVIEW must be updated with official URLs before public release.*
