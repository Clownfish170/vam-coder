import pytest
import shelf


def test_score_too_high():
    shelf.RECORDS.clear()
    with pytest.raises(ValueError):
        shelf.insert({"name": "a", "age": 20, "score": 101})


def test_score_negative():
    shelf.RECORDS.clear()
    with pytest.raises(ValueError):
        shelf.insert({"name": "a", "age": 20, "score": -1})


def test_score_ok():
    shelf.RECORDS.clear()
    shelf.insert({"name": "a", "age": 20, "score": 100})
    assert len(shelf.RECORDS) == 1


def test_page_regression():
    shelf.RECORDS.clear()
    for i in range(3):
        shelf.insert({"name": f"n{i}", "age": 20, "score": i})
    assert len(shelf.page(0, 2)) == 2
