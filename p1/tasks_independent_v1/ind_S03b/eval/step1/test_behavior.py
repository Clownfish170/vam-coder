import util
import text
import web


def test_moved():
    assert text.slugify("Hello World") == "hello-world"


def test_removed_from_util():
    assert not hasattr(util, "slugify")


def test_caller():
    assert web.page_title("Hello World") == "hello-world.html"


def test_util_still_has_shout():
    assert util.shout("ab") == "AB"
