"""Shapes."""


class Shape:
    def area(self):
        return 0

    def label(self):
        return "shape#0"


class Rect(Shape):
    def __init__(self, w, h):
        self.w = w
        self.h = h

    def area(self):
        return self.w * self.h

    def label(self):
        return f"rect#{self.area()}"


class Circle(Shape):
    def __init__(self, r):
        self.r = r

    def area(self):
        return 3.14 * self.r * self.r

    def label(self):
        return f"circle#{self.area()}"
