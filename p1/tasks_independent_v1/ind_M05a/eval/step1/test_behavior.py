import shapes


def test_circle_area():
    c = shapes.Circle(2)
    assert abs(c.area() - 12.56) < 1e-9
    assert c.label() == "circle"


def test_is_shape():
    assert isinstance(shapes.Circle(1), shapes.Shape)


def test_rect_regression():
    r = shapes.Rect(3, 4)
    assert r.area() == 12
    assert r.label() == "rect"
