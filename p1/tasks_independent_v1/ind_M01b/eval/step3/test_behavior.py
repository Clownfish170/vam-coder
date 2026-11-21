import grades
import report


def test_d_range():
    assert grades.letter(65) == "D"


def test_f_range():
    assert grades.letter(40) == "F"


def test_line_regression():
    assert report.line(8, 10) == "B"
