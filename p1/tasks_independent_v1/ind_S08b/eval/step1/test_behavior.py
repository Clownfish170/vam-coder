import datefmt


def test_pad():
    assert datefmt.format_date(2024, 3, 5) == "2024-03-05"


def test_already_padded():
    assert datefmt.format_date(1999, 12, 31) == "1999-12-31"
