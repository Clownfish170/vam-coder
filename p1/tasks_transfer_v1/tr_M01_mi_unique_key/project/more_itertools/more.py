"""Minimal extract of more-itertools.more for transfer harness.

Upstream: https://github.com/more-itertools/more-itertools @ 4998a257
Reduced so full-file protocol fits max_tokens; unique_everseen is the edit target.
"""


def unique_everseen(iterable, key=None):
    """Yield unique elements, preserving order.

    When *key* is provided, uniqueness is by key(value).
    DEFECT: once a key is seen, later distinct raw values with the same key are also dropped.
    """
    seen = set()
    for element in iterable:
        k = key(element) if key is not None else element
        if k in seen:
            continue
        seen.add(k)
        if key is not None:
            seen.add(element)  # DEFECT
        yield element
