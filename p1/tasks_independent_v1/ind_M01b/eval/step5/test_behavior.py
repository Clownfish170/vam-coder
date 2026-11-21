import report


def test_average():
    rows = [(8, 10), (9, 10)]
    assert report.average_score(rows) == 85.0


def test_average_empty():
    assert report.average_score([]) == 0.0


def test_line_regression():
    assert report.line(7, 10) == "C"
