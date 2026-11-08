"""Tiny store."""


class Bag:
    def __init__(self):
        self.items = []

    def put(self, k, v):
        self.items.append((k, v))

    def get(self, k):
        for kk, vv in reversed(self.items):
            if kk == k:
                return vv
        return None
