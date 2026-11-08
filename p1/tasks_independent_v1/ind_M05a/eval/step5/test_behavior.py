import shapes


def test_square():
    s = shapes.Square(5)
    assert s.area() == 25
    assert s.label() == "rect#25"
    assert isinstance(s, shapes.Rect)


def test_base_default_regression():
    import pytest
    with pytest.raises(NotImplementedError):
        shapes.Shape().area()


def test_triangle_regression():
    assert shapes.Triangle(6, 4).area() == 12
