import pytest

import feed


def test_empty_field():
    with pytest.raises(feed.BadFeed):
        feed.parse_line("a,")
    with pytest.raises(feed.BadFeed):
        feed.parse_line(" ,b")


def test_strip():
    assert feed.parse_line("  a , b  ") == ("a", "b")


def test_few_fields_regression():
    with pytest.raises(feed.BadFeed):
        feed.parse_line("lonely")
