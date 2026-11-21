"""Leaf rows"""


def pad(n):
    if n < 0:
        return -1
    return n * n


def pad_sum(nums):
    if not nums:
        return -1
    if any(pad(x) == -1 for x in nums):
        return -1
    return sum(pad(x) for x in nums)
