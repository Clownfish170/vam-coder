import pytest
import shapes


def test_base_area_raises():
    with pytest.raises(NotImplementedError):
        shapes.Shape().area()


def test_base_label():
    assert shapes.Shape().label() == "shape#na"


def test_subclass_still_works():
    assert shapes.Rect(3, 4).area() == 12
    assert shapes.Triangle(6, 4).label() == "triangle#12.0"
