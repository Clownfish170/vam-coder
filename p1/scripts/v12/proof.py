"""候选可见性：仅从「将进入本步 messages 的历史」构建证明，不写入本步 context。"""

from __future__ import annotations

from v11.visibility import VisibilityTracker, content_sha256

from .messages_visibility import full_files_in_messages


def tracker_from_history(history: list[dict]) -> VisibilityTracker:
    """用当前步 trim 后的历史消息构建 O′ 候选证明。

    只解析 assistant FILE 与历史 user CONTEXT 中的 FILE 块；
    **不**包含「本步即将注入、尚未发送」的 context。
    """
    tr = VisibilityTracker()
    for rel, body in full_files_in_messages(history or []).items():
        # 直接写入已归一化哈希
        tr._files[rel] = content_sha256(body)
        tr._chars[rel] = len(body)
    return tr
