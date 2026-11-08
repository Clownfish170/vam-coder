import pytest
import shelf
import views


def test_score_150_now_ok():
    shelf.RECORDS.clear()
    shelf.insert({"name": "a", "age": 20, "score": 150})
    assert len(shelf.RECORDS) == 1


def test_score_still_bounded():
    shelf.RECORDS.clear()
    with pytest.raises(ValueError):
        shelf.insert({"name": "a", "age": 20, "score": 201})


def test_summary_regression():
    shelf.RECORDS.clear()
    shelf.insert({"name": "ann", "age": 20, "score": 70})
    shelf.insert({"name": "bob", "age": 15, "score": 90})
    assert views.summary() == "2 total, 1 adult"
