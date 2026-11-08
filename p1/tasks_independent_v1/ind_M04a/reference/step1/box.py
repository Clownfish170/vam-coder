"""Box cache."""


class Box:
    def __init__(self, cap):
        self.cap = cap
        self.data = {}

    def put(self, k, v):
        if k not in self.data and len(self.data) >= self.cap:
            oldest = next(iter(self.data))
            del self.data[oldest]
        self.data[k] = v

    def get(self, k):
        return self.data.get(k)
