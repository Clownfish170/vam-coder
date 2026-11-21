import report


def test_total():
    assert report.total([(3, 4), (2, 2)]) == 16
