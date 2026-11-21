"""Sliding window."""


class Window:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buf = []

    def push(self, x):
        self.buf.append(x)
        if len(self.buf) > self.capacity:
            self.buf.pop(0)

    def values(self):
        return list(self.buf)
