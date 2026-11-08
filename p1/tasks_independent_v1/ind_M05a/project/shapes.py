"""Shapes."""


class Shape:
    def area(self):
        return 0

    def label(self):
        return "shape"


class Rect(Shape):
    def __init__(self, w, h):
        self.w = w
        self.h = h

    def area(self):
        return self.w * self.h

    def label(self):
        return "rect"
