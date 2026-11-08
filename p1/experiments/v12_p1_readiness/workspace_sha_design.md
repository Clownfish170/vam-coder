# Workspace SHA256 采集设计（P1）

状态：**方案 + 临时目录自测通过**；**未**改正式 runner。

## 1. 时序（每 Episode）

```text
copy frozen p1/tasks/<id>/project → workspaces/<episode_id>/
→ workspace_pre_manifest.json     # 首次模型请求前
→ step1 … stepN（同 workspace）
→ workspace_post_manifest.json    # episode 结束
→ workspace_diff.json
```

## 2. Manifest 字段

```json
{
  "episode_id": "v1_RUR02_E_R3",
  "task_id": "v1_RUR02",
  "arm": "E",
  "repetition": 3,
  "timestamp": "ISO8601",
  "files": [
    {"relative_path": "hot.py", "file_size": 12, "sha256": "..."}
  ],
  "total_files": 3,
  "total_bytes": 40,
  "manifest_sha256": "sha256(json.dumps(files, sort_keys=True))"
}
```

## 3. Diff 分类

| 类 | 规则 |
| --- | --- |
| ADDED | post 有 pre 无 |
| DELETED | pre 有 post 无 |
| MODIFIED | 双方有且 sha 不同 |
| UNCHANGED | 双方有且 sha 相同 |

## 4. 隔离约束

- 每 episode 独立目录；Arm 不共享可写盘  
- 源 `p1/tasks/**` 只读  
- pre 必须在第一次 `chat_completion` **之前**落盘  
- 禁止用事后清单冒充 pre 证据  

## 5. 自测

脚本：`_ws_sha_selftest.py`  
结果：`workspace_sha_test_result.json`  

| 检查 | 结果 |
| --- | --- |
| ADDED/MODIFIED/DELETED | True |
| sha 独立复算 | True |
| manifest 稳定 | True |

**注意**：Windows `write_text` 可能产生 CRLF；自测用 `write_bytes`。正式实现须统一字节级读写。

## 6. 正式实现缺口（未授权改码）

`run_p1_v12.py` **尚未**调用本设计。  
P1 若要求逐集 SHA 对账，需 **另行授权** 修改 runner（最小 diff：step0/step end 写 manifest）。
