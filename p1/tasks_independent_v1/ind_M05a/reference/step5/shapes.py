"""Shapes."""


class Shape:
    def area(self):
        raise NotImplementedError("area")

    def label(self):
        return "shape#na"


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


class Triangle(Shape):
    def __init__(self, base, height):
        self.base = base
        self.height = height

    def area(self):
        return self.base * self.height / 2

    def label(self):
        return f"triangle#{self.area()}"


class Square(Rect):
    def __init__(self, side):
        super().__init__(side, side)
