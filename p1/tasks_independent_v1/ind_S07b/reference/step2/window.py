"""Sliding window."""


class Window:
    def __init__(self, capacity):
        self.capacity = capacity
        self.ring = [None] * capacity
        self.count = 0
        self.head = 0

    def push(self, x):
        idx = (self.head + self.count) % self.capacity
        if self.count == self.capacity:
            self.ring[self.head] = x
            self.head = (self.head + 1) % self.capacity
        else:
            self.ring[idx] = x
            self.count += 1

    def values(self):
        out = []
        for i in range(self.count):
            out.append(self.ring[(self.head + i) % self.capacity])
        return out

    def size(self):
        return self.count
