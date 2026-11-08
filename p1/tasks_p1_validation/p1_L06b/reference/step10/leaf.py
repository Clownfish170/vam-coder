"""Leaf cells"""


def grow(n):
    if n < 0:
        return -1
    return n * n


def grow_sum(nums):
    if not nums:
        return -1
    if any(grow(x) == -1 for x in nums):
        return -1
    return sum(grow(x) for x in nums)
