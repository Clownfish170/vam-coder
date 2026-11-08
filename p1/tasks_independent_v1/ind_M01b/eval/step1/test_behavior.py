import grades


def test_pct_scale():
    assert grades.pct(9, 10) == 90.0


def test_pct_full():
    assert grades.pct(10, 10) == 100.0


def test_letter_regression():
    assert grades.letter(85) == "B"
