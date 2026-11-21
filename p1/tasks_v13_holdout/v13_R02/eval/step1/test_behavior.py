import math
import pytest
from shapes import Circle, Rect


def test_scale_ok():
    c = Circle(2)
    c.scale(3)
    assert abs(c.area() - math.pi * 36) < 1e-6


def test_invalid_zero_factor():
    with pytest.raises(ValueError):
        Circle(1).scale(0)


def test_invalid_negative_factor():
    with pytest.raises(ValueError):
        Rect(1, 1).scale(-1)
