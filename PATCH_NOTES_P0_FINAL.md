# PATCH_NOTES_P0_FINAL —— VAM-Coder P0 最终轮（解析器两问题）

- 日期：2026-10-16
- 前序：轮 1 修复（A–G）见 `PATCH_NOTES.md`；修复前基线 git `37bf61c`。
- 本轮起点：轮 1 完成态，全量 63 passed / 场景 6/6（存档
  `results/p0_final_pre_fix_pytest.txt`，exit 0）。
- 范围：仅两个已知解析器问题 + 针对性回归测试。不训练模型、不接真实 KV、
  不做学习式路由器、不大规模重构；未覆盖/删除原始测试记录、日志与数据库
  （本轮新结果全部使用新文件名 `p0_final_*`）。

---

## 1. 修改文件清单与修复原因

### `src/vam_coder/parser.py`（任务 1 + 任务 2）
| 变更 | 原因 |
|---|---|
| 状态值重命名：`parsed/read_error` → **`success`/`failed`**（`partial`、`unsupported_language` 不变）；`CONFIRMED_STATUSES={success}` | 任务 1 要求明确区分 success/partial/failed/unsupported_language；错误原因仍保留在 `file_errors`/`parse_warnings`（`read_error: …`、`tree_sitter_has_error`） |
| 模块 docstring：partial 的**非权威**语义、局部 import 不泄漏、裸名解析顺序与抑制规则、`unresolved` 记 `detail` | 任务 1/2 的规则文本化（审计依据） |
| `extract_import_bindings()` 重写：返回 `{"module": {…}, "local": {符号限定名: {…}}}`；新增 `_indexed_symbol_qname` / `_enclosing_indexed_qname` 判定导入归属（模块级 vs 函数/类局部；嵌套函数计入其被索引的外层符号；方法归属 `Class.method`） | 任务 2：旧实现全树平铺 → 函数内 import 泄漏给同文件其他函数 |
| `_file_scope_bindings()` + `_resolve_call()` 重写为三元返回 `(target, reason, detail)`；裸名顺序：**本符号局部 import → 模块级 import（与同文件 def 冲突=ambiguous）→ 同文件模块级定义 → 抑制规则（他符号局部 import 证据 → unresolved+detail）→ 全局唯一裸名 → unresolved**；属性调用的 import 查找同样分局部/模块级 | 任务 2：局部作用域可见性 + “不可靠即 unresolved，不猜测” |
| `resolve_dependencies()` 消费分层绑定并输出 `detail` | 任务 2 可审计原因 |

### `src/vam_coder/invalidation.py`（任务 1）
| 变更 | 原因 |
|---|---|
| `SyncOutcome` 新增 `incomplete_symbols`（并入 `sync_completed` 日志） | 任务 1.5：部分文件新符号的诊断保留（明确“未注册”） |
| `sync_parsed` 阶段 A0：草稿按 `file_status` 分层，**只有 success 文件的草稿**进入分类（insert/change/revert/deps_refresh/unchanged/tombstone 判定） | 任务 1.2/1.3：部分 AST 不得更新内容依据、依赖边、版本与删除判定 |
| 阶段 A2：partial 草稿 → 既有 valid 符号收紧 unconfirmed（reason `file_partial`，沿用不传播种子规则）；新符号只进 `incomplete_symbols` **不注册**；缺失误 tombstone 由缺失循环跳过 `incomplete_ids` 保证 | 任务 1.3/1.4/1.5 |
| `_deps_with_unconfirmable_held()`：旧依赖边的目标文件若处于 partial/failed/unsupported（或受支持语言失效），**无法确认目标消失 → 保留该边**；用于 unchanged 漂移、change、revert 三处 deps 写入 | 任务 1.3“不得用部分结果覆盖依赖图”——修复前完整文件 `app.py` 因 partial 目标丢失 `helper` 提取而被清边（新测试复现） |
| `verify._verify_locked`：`has_error` **一律** `verify_inconclusive`（即使符号被部分提取），不再写 stale/tombstone/恢复；根校验/文件消失/读失败/unsupported 语义保持 | 任务 1.2/1.3 的 verify 侧——修复前“部分提取+哈希失配→写 stale”属部分 AST 当权威 |
| `_absence_fate`/docstring 同步 status 命名与 partial 政策 | 一致性 |

### `src/vam_coder/pipeline.py`
- 仅文档：`sync_repo` 说明 success 唯一权威（任务 1 要求检查该文件；流程编排
  本身无行为变化）。

### `tests/test_parse_guard.py`（唯一调整的既有测试）
- `file_read_error` → `file_failed`：状态值重命名的配套断言，**断言强度不变**
  （仍要求原因精确匹配）。其余 63 项既有测试未删除、未 skip、未弱化。

### `README.md`（交付 E）
- §1 测试数量与存档；§3 新测试文件；§4.1 解析状态四态 + partial 政策 +
  import 作用域边界；§4.3 失效规则表两行；§6 已知限制 5/6 改写；
- §7 两轮结果与最终轮复现记录；§8 准入条件；§9 命令速查。

### 未修改
`store.py`、`router.py`、`models.py`、`logging_util.py`、`config.py`、
`hashing.py`、`scripts/run_p0_scenario.py`、`config/default.json`、
`pytest.ini`、`requirements.txt`（两问题均不涉及；场景脚本原样通过）。

---

## 2. 新增测试与“如何复现旧问题”

执行顺序（符合要求 8）：先跑既有测试记录 → 写新测试 → **在修复前代码上
运行新测试记录失败** → 实施修复 → 全量复跑。

- 修复前既有测试：63 passed，exit 0 → `results/p0_final_pre_fix_pytest.txt`
- **新测试 vs 修复前代码**：`tests/test_partial_parse_authority.py`(6) +
  `tests/test_import_scoping.py`(7) → **11 failed，2 passed，exit 1** →
  `results/p0_final_repro_on_prev.txt`。复现对照：

| 测试 | 修复前行为（失败原因 = 旧缺陷） |
|---|---|
| `test_partial_changed_file_does_not_update_memory_basis` | 部分 AST 中提取的 compute 被当权威 → 判 stale/覆盖 source_hash/或依赖被清 |
| `test_partial_missing_symbol_not_tombstoned` | partial 文件中缺失的 lone 被 tombstone |
| `test_new_symbols_in_partial_file_not_registered` | partial 文件新符号 extra/broken 被 insert 注册 |
| `test_recovery_after_parse_fixed_resumes_authoritative_sync` | 冻结阶段即产生 content_changed（未冻结） |
| `test_verify_partial_parse_inconclusive_even_if_symbol_extracted` | 符号被部分提取 → verify 直接写 stale 并 bump 版本 |
| `test_parse_statuses_recorded_per_file` | 状态值为 `parsed` 而非 `success`（API 重命名） |
| `test_local_import_scoped_to_its_function` | function_b 因 function_a 的局部 import 被连到 module_a.helper |
| `test_local_import_does_not_disambiguate_sibling` | 同上（且跨文件同名场景被误消歧） |
| `test_local_import_alias_scoped` | 局部 alias `h` 泄漏给 function_b |
| `test_local_import_shadows_same_file_module_def_inside_function` | 函数内局部 import 未优先（被模块级冲突规则拦下或泄漏方向错误） |
| `test_nested_function_local_import_attributed_to_outer` | sibling 被外层嵌套函数的局部 import 影响 |
| `test_module_level_import_and_alias_still_work`（通过） | 修复前即正确 → 防回归 |
| `test_local_import_of_missing_module_is_unresolved`（通过） | 修复前也无边（目标缺失），原因表述不同 → 防回归 |

---

## 3. 实测结果与退出码

| 命令 | 结果 | 退出码 | 存档 |
|---|---|---|---|
| 既有测试（本轮修复前） | 63 passed | 0 | `results/p0_final_pre_fix_pytest.txt` |
| 新测试 × 修复前代码（复现） | 11 failed, 2 passed | 1 | `results/p0_final_repro_on_prev.txt` |
| `python -m pytest tests/ -v --tb=short`（修复后全量） | **76 passed** | **0** | `results/p0_final_pytest.txt` |
| `python scripts/run_p0_scenario.py`（修复后） | **6/6 PASS, ALL PASSED: True** | **0** | `results/p0_final_scenario.txt` |
| 退出码汇总 | — | 0 / 0 | `results/p0_final_exit_codes.txt` |

环境依赖齐全（tree-sitter 0.26.0 / tree-sitter-python 0.25.0 / blake3 /
pytest 9.1.1，Python 3.12.10，Windows win32），**无未验证项**。

## 4. 本轮仍未处理（移交 P0 冻结清单 / P1）

- 绑定执行顺序（def 与 import 先后）、条件导入可达性、重导出链、
  wildcard 消解：明确不支持 → unresolved（README §6.5）。
- 嵌套函数局部 import 归属外层为**近似**（有测试钉住）；类体内 import
  仅归属类符号本身，方法不继承（README §6.5）。
- 部分解析文件在恢复 success 前记忆保持冻结；指向它的依赖边被保留
  （可能短暂高估覆盖）——恢复后一次性推进（README §6.6）。
- 依赖闭包深度截断、循环依赖活性、事务-JSONL 非原子等轮 1 遗留限制
  不变（见 `results/p0_fix_report.md` §3 与 `results/p0_final_acceptance.md`）。
