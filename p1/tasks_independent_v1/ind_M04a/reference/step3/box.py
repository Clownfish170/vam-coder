"""Box cache."""


class Box:
    def __init__(self, cap):
        self.cap = cap
        self.data = {}
        self.hits = 0
        self.misses = 0

    def put(self, k, v):
        if k in self.data:
            del self.data[k]
        elif len(self.data) >= self.cap:
            oldest = next(iter(self.data))
            del self.data[oldest]
        self.data[k] = v

    def get(self, k):
        if k in self.data:
            v = self.data.pop(k)
            self.data[k] = v
            self.hits += 1
            return v
        self.misses += 1
        return None
