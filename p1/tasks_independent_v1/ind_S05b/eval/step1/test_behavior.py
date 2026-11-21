import pytest

import feed


def test_too_few():
    with pytest.raises(feed.BadFeed):
        feed.parse_line("lonely")


def test_ok():
    assert feed.parse_line("a,b") == ("a", "b")
