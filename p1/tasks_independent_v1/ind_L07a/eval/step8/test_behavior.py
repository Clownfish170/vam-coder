import shelf
import views


def _seed():
    shelf.RECORDS.clear()
    shelf.insert({"name": "ann", "age": 20, "score": 70})
    shelf.insert({"name": "bob", "age": 15, "score": 90})


def test_summary():
    _seed()
    assert views.summary() == "2 total, 1 adult"


def test_summary_empty():
    shelf.RECORDS.clear()
    assert views.summary() == "0 total, 0 adult"


def test_top_regression():
    _seed()
    assert views.top_names(1) == ["bob"]


def test_adults_regression():
    _seed()
    assert [r["name"] for r in shelf.adults()] == ["ann"]
