import pytest

import datefmt


def test_parse():
    assert datefmt.parse_date("2024-03-05") == (2024, 3, 5)


def test_parse_bad():
    with pytest.raises(ValueError):
        datefmt.parse_date("2024/03/05")
    with pytest.raises(ValueError):
        datefmt.parse_date("not-a-date")


def test_format_regression():
    assert datefmt.format_date(2024, 3, 5) == "2024-03-05"
