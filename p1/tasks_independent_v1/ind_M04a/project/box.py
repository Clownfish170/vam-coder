"""Box cache."""


class Box:
    def __init__(self, cap):
        self.cap = cap
        self.data = {}

    def put(self, k, v):
        self.data[k] = v

    def get(self, k):
        return self.data.get(k)
