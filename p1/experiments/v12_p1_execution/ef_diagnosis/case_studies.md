# E vs F Case Studies

## v1_CFD03 R1 → F_only
- E success=0 tokens=544; F success=1 tokens=561
  - E step1: eval=1 prompt=184 full=0 idx=1 no_edit=False resp='FILE: util.py | ```python | def clamp(value, lo, hi): |     if not (lo <= va'
  - E step2: eval=0 prompt=262 full=1 idx=0 no_edit=False resp='FILE: app.py | ```python | from util import clamp |  |  | def norm(x): |     retur'
  - evidence: `runs/v1_CFD03_E_R1/runner_out/episodes/...`
  - F step1: eval=1 prompt=207 full=1 idx=0 no_edit=False resp='FILE: util.py | ```python | def clamp(x, lo, hi): |     if lo > hi: |         '
  - F step2: eval=1 prompt=259 full=1 idx=0 no_edit=False resp='FILE: app.py | ```python | from util import clamp |  |  | def norm(x): |     retur'
  - evidence: `runs/v1_CFD03_F_R1/runner_out/episodes/...`
## v1_CFD03 R2 → F_only
- E success=0 tokens=544; F success=1 tokens=561
  - E step1: eval=1 prompt=184 full=0 idx=1 no_edit=False resp='FILE: util.py | ```python | def clamp(value, lo, hi): |     if not (lo <= va'
  - E step2: eval=0 prompt=262 full=1 idx=0 no_edit=False resp='FILE: app.py | ```python | from util import clamp |  |  | def norm(x): |     retur'
  - evidence: `runs/v1_CFD03_E_R2/runner_out/episodes/...`
  - F step1: eval=1 prompt=207 full=1 idx=0 no_edit=False resp='FILE: util.py | ```python | def clamp(x, lo, hi): |     if lo > hi: |         '
  - F step2: eval=1 prompt=259 full=1 idx=0 no_edit=False resp='FILE: app.py | ```python | from util import clamp |  |  | def norm(x): |     retur'
  - evidence: `runs/v1_CFD03_F_R2/runner_out/episodes/...`
## v1_CFD03 R3 → F_only
- E success=0 tokens=544; F success=1 tokens=561
  - E step1: eval=1 prompt=184 full=0 idx=1 no_edit=False resp='FILE: util.py | ```python | def clamp(value, lo, hi): |     if not (lo <= va'
  - E step2: eval=0 prompt=262 full=1 idx=0 no_edit=False resp='FILE: app.py | ```python | from util import clamp |  |  | def norm(x): |     retur'
  - evidence: `runs/v1_CFD03_E_R3/runner_out/episodes/...`
  - F step1: eval=1 prompt=207 full=1 idx=0 no_edit=False resp='FILE: util.py | ```python | def clamp(x, lo, hi): |     if lo > hi: |         '
  - F step2: eval=1 prompt=259 full=1 idx=0 no_edit=False resp='FILE: app.py | ```python | from util import clamp |  |  | def norm(x): |     retur'
  - evidence: `runs/v1_CFD03_F_R3/runner_out/episodes/...`
## v1_RFS01 R1 → F_only
- E success=0 tokens=548; F success=1 tokens=607
  - E step1: eval=0 prompt=239 full=2 idx=0 no_edit=False resp='FILE: mode.py | ```python | """Mode.""" | ```'
  - E step2: eval=1 prompt=229 full=2 idx=0 no_edit=False resp='FILE: app.py | ```python | from mode import describe, is_active |  |  | def bann'
  - evidence: `runs/v1_RFS01_E_R1/runner_out/episodes/...`
  - F step1: eval=1 prompt=239 full=2 idx=0 no_edit=False resp='FILE: app.py | ```python | from mode import describe |  |  | def banner(): |     r'
  - F step2: eval=1 prompt=261 full=1 idx=0 no_edit=False resp='FILE: app.py | ```python | from mode import describe |  |  | def banner(): |     r'
  - evidence: `runs/v1_RFS01_F_R1/runner_out/episodes/...`
## v1_RFS01 R2 → E_only
- E success=1 tokens=607; F success=0 tokens=548
  - E step1: eval=1 prompt=239 full=2 idx=0 no_edit=False resp='FILE: app.py | ```python | from mode import describe |  |  | def banner(): |     r'
  - E step2: eval=1 prompt=261 full=1 idx=0 no_edit=False resp='FILE: app.py | ```python | from mode import describe |  |  | def banner(): |     r'
  - evidence: `runs/v1_RFS01_E_R2/runner_out/episodes/...`
  - F step1: eval=0 prompt=239 full=2 idx=0 no_edit=False resp='FILE: mode.py | ```python | """Mode.""" | ```'
  - F step2: eval=1 prompt=229 full=2 idx=0 no_edit=False resp='FILE: app.py | ```python | from mode import describe, is_active |  |  | def bann'
  - evidence: `runs/v1_RFS01_F_R2/runner_out/episodes/...`
