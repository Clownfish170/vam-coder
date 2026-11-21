"""Leaf units"""


def norm(n):
    if n < 0:
        return -1
    return n * n


def sum_all(nums):
    if not nums:
        return -1
    return sum(norm(x) for x in nums)
