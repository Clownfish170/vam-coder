import shelf
import views


def _seed():
    shelf.RECORDS.clear()
    shelf.insert({"name": "ann", "age": 20, "score": 70})
    shelf.insert({"name": "bob", "age": 15, "score": 90})
    shelf.insert({"name": "cyd", "age": 30, "score": 40})


def test_top_names():
    _seed()
    assert views.top_names(2) == ["bob", "ann"]


def test_top_names_all():
    _seed()
    assert views.top_names(10) == ["bob", "ann", "cyd"]


def test_heading_regression():
    assert views.heading() == "shelf"


def test_filter_regression():
    _seed()
    assert [r["name"] for r in shelf.filter_by(70)] == ["ann", "bob"]
