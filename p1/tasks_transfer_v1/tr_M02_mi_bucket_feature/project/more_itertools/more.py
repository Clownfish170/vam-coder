"""Minimal extract of more-itertools.more for transfer harness.

Upstream: https://github.com/more-itertools/more-itertools @ 4998a257
bucket_into is intentionally absent — the task requires adding it.
"""


def chunked(iterable, n):
    """Yield lists of length n."""
    it = iter(iterable)
    while True:
        chunk = []
        for _ in range(n):
            try:
                chunk.append(next(it))
            except StopIteration:
                break
        if not chunk:
            return
        yield chunk
