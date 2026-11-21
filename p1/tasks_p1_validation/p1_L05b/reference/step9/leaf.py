"""Leaf keys"""


def fold(n):
    if n < 0:
        return -1
    return n * n


def fold_sum(nums):
    if not nums:
        return -1
    if any(fold(x) == -1 for x in nums):
        return -1
    return sum(fold(x) for x in nums)
