import pytest

import kv


def test_line():
    assert kv.parse_line("a=1;b=2") == {"a": "1", "b": "2"}


def test_line_bad_segment():
    with pytest.raises(ValueError):
        kv.parse_line("a=1;oops")


def test_pair_regression():
    assert kv.parse_pair("a=1") == ("a", "1")
