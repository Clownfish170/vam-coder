"""Shelf cache."""


class Shelf:
    def __init__(self, slots):
        self.slots = slots
        self.entries = []

    def store(self, tag, val):
        self.entries.append((tag, val))

    def fetch(self, tag):
        for t, v in reversed(self.entries):
            if t == tag:
                return v
        return None
