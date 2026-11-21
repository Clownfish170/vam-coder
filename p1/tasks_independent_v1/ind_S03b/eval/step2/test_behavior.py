import text
import util


def test_slug_list():
    assert text.slug_list(["A B", "c d"]) == ["a-b", "c-d"]


def test_move_regression():
    assert text.slugify("X Y") == "x-y"
    assert not hasattr(util, "slugify")


def test_wrap_regression():
    assert text.wrap("abcdef", 3) == "abc"
