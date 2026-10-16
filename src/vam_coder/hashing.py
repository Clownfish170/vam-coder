"""内容哈希：默认 blake3（报告 §4.4），可退化到 blake2b。"""

from __future__ import annotations

import hashlib


def content_hash(data: bytes, algo: str = "blake3") -> str:
    if algo == "blake3":
        from blake3 import blake3

        return blake3(data).hexdigest()
    if algo == "blake2b":
        return hashlib.blake2b(data, digest_size=32).hexdigest()
    raise ValueError(f"unsupported hash algo: {algo!r} (expected blake3|blake2b)")
