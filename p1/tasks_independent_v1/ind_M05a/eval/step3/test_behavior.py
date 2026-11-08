import shapes


def test_triangle():
    t = shapes.Triangle(6, 4)
    assert t.area() == 12
    assert t.label() == "triangle#12.0"


def test_is_shape():
    assert isinstance(shapes.Triangle(1, 1), shapes.Shape)


def test_label_format_regression():
    assert shapes.Rect(3, 4).label() == "rect#12"
