import geo


def test_padded_area_uses_margin():
    assert abs(geo.padded_area(10, 10) - 110.0) < 1e-9


def test_padded_area_small():
    assert abs(geo.padded_area(4, 5) - 22.0) < 1e-9


def test_border_regression():
    assert abs(geo.border_area(2, 2) - 2.1 * 2.1) < 1e-9
