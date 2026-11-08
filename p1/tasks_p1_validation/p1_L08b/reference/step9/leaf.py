"""Leaf frames"""


def render_n(n):
    if n < 0:
        return -1
    return n * n


def render_sum(nums):
    if not nums:
        return -1
    if any(render_n(x) == -1 for x in nums):
        return -1
    return sum(render_n(x) for x in nums)
