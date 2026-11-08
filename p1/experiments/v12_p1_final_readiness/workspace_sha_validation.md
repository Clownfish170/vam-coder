# Workspace SHA256 证据链验证

## 1. 独立临时测试（本轮实测）

| 操作 | 结果 |
| --- | --- |
| 创建 a.py, b.py | pre manifest 2 files |
| 修改 a.py / 新增 c.py / 删除 b.py | post manifest |
| **ADDED** | `['c.py']` **PASS** |
| **MODIFIED** | `['a.py']` **PASS** |
| **DELETED** | `['b.py']` **PASS** |
| **UNCHANGED** | 空（本例无不变文件）**PASS** |
| SHA256 复算 | 字节级一致 **PASS** |
| 字段 episode/task/arm/rep/timestamp/files/total/manifest_sha | **PASS** |

辅助脚本：`../v12_p1_readiness/_ws_sha_selftest.py`（及本目录复算）。

**Windows 注意**：`write_text` 可能 CRLF；证据链须 **字节读写**。

---

## 2. 正式实现缺口

| 检查 | 结果 |
| --- | --- |
| `run_p1_v12.py` 含 `workspace_pre_manifest` | **否**（`pre_manifest in runner = False`） |
| P1 每集 pre/post/diff 自动落盘 | **NOT_IMPLEMENTED** |
| 跨 Episode 隔离（目录 copytree） | **PASS**（结构，P0 32 workspaces） |
| 冻结任务源只读 | **PASS**（未改 tasks） |
| 事后补录冒充 pre 的风险 | **存在**若无强制 step0 落盘 → **P1 级风险** |

---

## 3. 最小实现建议（未授权，不改码）

| 项 | 建议 |
| --- | --- |
| 文件 | `run_p1_v12.py`（及 A/B/D 入口若纳入 P1） |
| 调用点 | copytree 后、第一次 chat 前 → `workspace_pre_manifest.json` |
| 结束点 | episode 汇总后 → `post` + `diff` |
| 字段 | 见 workspace_sha_design（相对路径/size/sha256/ids/time/manifest_sha256） |
| 单测 | 临时目录 ADDED/MODIFIED/DELETED/UNCHANGED + 独立复算 |
| 是否 P1 前必须 | **数据质量 P1 级**：用户可选“必须实现”或“书面接受无 pre-manifest” |

**Workspace SHA：CONDITIONAL**（方案自测 PASS；正式钩子未接）。
