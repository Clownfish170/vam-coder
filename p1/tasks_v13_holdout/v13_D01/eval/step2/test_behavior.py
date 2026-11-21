import geo


def test_padded_perimeter():
    assert abs(geo.padded_perimeter(10, 20) - 66.0) < 1e-9


def test_padded_area_regression():
    assert abs(geo.padded_area(10, 10) - 110.0) < 1e-9
