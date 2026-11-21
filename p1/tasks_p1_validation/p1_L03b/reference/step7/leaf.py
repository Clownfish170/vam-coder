"""Leaf tokens"""


def embed(n):
    if n < 0:
        return -1
    return n * n


def embed_sum(nums):
    if not nums:
        return -1
    return sum(embed(x) for x in nums)
