import geom, report


def test_area():
    assert geom.area((3, 4)) == 12


def test_line():
    assert report.line(3, 4) == '12 u2'
