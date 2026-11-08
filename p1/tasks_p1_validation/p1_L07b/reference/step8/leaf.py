"""Leaf stats"""


def meanish(n):
    if n < 0:
        return -1
    return n * n


def mean_sum(nums):
    if not nums:
        return -1
    return sum(meanish(x) for x in nums)
