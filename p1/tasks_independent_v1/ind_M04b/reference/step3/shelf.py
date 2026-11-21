"""Shelf cache."""


class Shelf:
    def __init__(self, slots):
        self.slots = slots
        self.entries = []
        self.hits = 0
        self.misses = 0

    def store(self, tag, val):
        self.entries = [(t, v) for t, v in self.entries if t != tag]
        if len(self.entries) >= self.slots:
            self.entries.pop(0)
        self.entries.append((tag, val))

    def fetch(self, tag):
        for i in range(len(self.entries) - 1, -1, -1):
            if self.entries[i][0] == tag:
                t, v = self.entries.pop(i)
                self.entries.append((t, v))
                self.hits += 1
                return v
        self.misses += 1
        return None
