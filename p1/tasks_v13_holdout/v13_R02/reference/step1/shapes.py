"""Shape primitives."""

import math


class Circle:
    def __init__(self, r):
        self.r = r

    def area(self):
        return math.pi * self.r * self.r

    def scale(self, factor):
        if factor <= 0:
            raise ValueError("factor must be > 0")
        self.r *= factor
        return self


class Rect:
    def __init__(self, w, h):
        self.w = w
        self.h = h

    def area(self):
        return self.w * self.h

    def scale(self, factor):
        if factor <= 0:
            raise ValueError("factor must be > 0")
        self.w *= factor
        self.h *= factor
        return self
