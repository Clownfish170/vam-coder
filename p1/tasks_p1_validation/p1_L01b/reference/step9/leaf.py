"""Leaf math"""


def shape(n):
    if n < 0:
        return -1
    return n * n


def total(nums):
    if not nums:
        return -1
    if any(shape(x) == -1 for x in nums):
        return -1
    return sum(shape(x) for x in nums)
