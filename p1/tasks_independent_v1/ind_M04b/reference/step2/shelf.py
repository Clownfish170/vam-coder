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
        for t, v in reversed(self.entries):
            if t == tag:
                self.hits += 1
                return v
        self.misses += 1
        return None
