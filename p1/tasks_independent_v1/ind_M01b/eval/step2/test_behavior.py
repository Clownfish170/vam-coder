import report
import grades


def test_line_ok():
    assert report.line(8, 10) == "B"


def test_line_high():
    assert report.line(9, 10) == "A"


def test_pct_regression():
    assert grades.pct(7, 10) == 70.0
