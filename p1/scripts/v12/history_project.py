"""V13E·S1 状态投影：历史 assistant FILE 块按路径折叠。

背景（见 p1/docs/v13e_sah_design.md §3）：
- 阶段 A `tracker_from_history` 与阶段 B `verify_omissions_in_messages` 提取历史文件
  用的是同一个 `full_files_in_messages`，语义为**按归一化路径后写覆盖的 dict**。
- 因此任何**保留了每路径最后一次出现**的子集，对可见性提取结果**零影响**：
  O′ 候选证明、省略授权、发送前 PreSendCheck 全部逐字段不变。

mode：
- ``last``：每路径只保留最后一次出现（省得最多）。
- ``first_last``：保留首版 + 末版，折叠中间版。1.5B 筛选 ind_M04a 显示
  「仅留末版」会改变贪心解码轨迹（模型改写丢行 → ESR 丢失），保留首版
  以留住编辑轨迹端点；两种 mode 都保留末版，故 O′ 等价性同样成立。

规则：
1. 只处理 role=assistant 且匹配 `FILE: path\\n``` … ``` ` 的块；其余消息原样保留。
2. 不在保留集合内的块 → 正文替换为折叠标记。
3. 折叠标记不含 `FILE:` 前缀与围栏，不会被 `_ASSIST_FILE_RE` 重新匹配。

投影是纯函数：默认关闭时不参与任何调用路径，既有臂行为逐字节不变。
"""

from __future__ import annotations

from v11.visibility import _norm_path
from v12.messages_visibility import _ASSIST_FILE_RE

# 标记文本：不出现 `FILE:` + 围栏，不携带任何文件正文
FOLD_FMT_LAST = "（历史折叠）{path} 的较早版本已省略，仅保留其最新版本。"
FOLD_FMT_FIRST_LAST = "（历史折叠）{path} 的中间版本已省略，保留其首版与最新版本。"
FOLD_FMT_KEEP_K = "（历史折叠）{path} 的更早版本已省略，保留其最近 {keep} 版。"
# 档位（dial）：保留策略 = 末版必留 + 按档位追加
#   last        仅末版（省得最多；轨迹扰动最大）
#   first_last  首版+末版（M04a 修复候选）
#   last2/last3 保留最近 2/3 版（更贴近全量轨迹，省得更少）
MODES = ("last", "first_last", "first_last2", "last2", "last3")
_KEEP_K = {"first_last2": 2, "last2": 2, "last3": 3}


def fold_marker(path: str, mode: str = "last") -> str:
    if mode == "first_last":
        return FOLD_FMT_FIRST_LAST.format(path=path)
    if mode in _KEEP_K:
        keep = "首版+" if mode.startswith("first") else ""
        return FOLD_FMT_KEEP_K.format(path=path, keep=f"{keep}{_KEEP_K[mode]}")
    return FOLD_FMT_LAST.format(path=path)


def project_history(
    history: list[dict], mode: str = "last"
) -> tuple[list[dict], dict]:
    """按路径折叠历史 FILE 块。

    返回 (投影后消息列表, 统计)；统计含
    folded_blocks / kept_blocks / chars_before / chars_after。
    """
    if mode not in MODES:
        raise ValueError(f"unknown project mode: {mode!r} (expected one of {MODES})")
    msgs = list(history or [])

    # Pass 1：解析每个 assistant 消息的 FILE 块，按路径记录出现次序
    matches_per_msg: list[list] = [[] for _ in msgs]
    occ: dict[str, list[tuple[int, int]]] = {}
    for i, m in enumerate(msgs):
        if m.get("role") != "assistant":
            continue
        content = m.get("content")
        if not isinstance(content, str) or not content:
            continue
        for j, mo in enumerate(_ASSIST_FILE_RE.finditer(content)):
            path = _norm_path(mo.group("path"))
            matches_per_msg[i].append((j, path, mo))
            occ.setdefault(path, []).append((i, j))

    # 保留集合：末版必留；按档位追加（首版 / 最近 K 版）
    keep_at: set[tuple[int, int]] = set()
    for positions in occ.values():
        keep_at.add(positions[-1])
        if mode == "first_last":
            keep_at.add(positions[0])
        elif mode == "first_last2":
            keep_at.add(positions[0])
            for pos in positions[-2:]:
                keep_at.add(pos)
        elif mode in _KEEP_K:
            for pos in positions[-_KEEP_K[mode] :]:
                keep_at.add(pos)

    chars_before = 0
    chars_after = 0
    folded = 0
    kept = 0
    out: list[dict] = []
    for i, m in enumerate(msgs):
        content = m.get("content")
        blocks = matches_per_msg[i]
        if not isinstance(content, str) or not content:
            out.append(m)
            continue
        chars_before += len(content)
        if not blocks:
            chars_after += len(content)
            out.append(m)
            continue
        pieces: list[str] = []
        cursor = 0
        changed = False
        for j, path, mo in blocks:
            if (i, j) in keep_at:
                kept += 1
                continue
            pieces.append(content[cursor : mo.start()])
            pieces.append(fold_marker(path, mode))
            cursor = mo.end()
            folded += 1
            changed = True
        if not changed:
            chars_after += len(content)
            out.append(m)
            continue
        pieces.append(content[cursor:])
        new_content = "".join(pieces)
        chars_after += len(new_content)
        out.append({**m, "content": new_content})
    return out, {
        "folded_blocks": folded,
        "kept_blocks": kept,
        "chars_before": chars_before,
        "chars_after": chars_after,
        "mode": mode,
    }
