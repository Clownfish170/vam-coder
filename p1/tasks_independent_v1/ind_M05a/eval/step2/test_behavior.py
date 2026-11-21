import shapes


def test_rect_label():
    assert shapes.Rect(3, 4).label() == "rect#12"


def test_circle_label():
    assert shapes.Circle(2).label() == "circle#12.56"


def test_base_label():
    assert shapes.Shape().label() == "shape#0"


def test_area_regression():
    assert shapes.Rect(2, 5).area() == 10
