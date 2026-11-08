import pytest
import shelf


def _seed():
    shelf.RECORDS.clear()
    shelf.insert({"name": "ann", "age": 20, "score": 70})
    shelf.insert({"name": "bob", "age": 15, "score": 90})
    shelf.insert({"name": "cyd", "age": 30, "score": 40})


def test_filter_by():
    _seed()
    out = shelf.filter_by(70)
    assert [r["name"] for r in out] == ["ann", "bob"]


def test_filter_by_none():
    _seed()
    assert shelf.filter_by(100) == []


def test_duplicate_regression():
    shelf.RECORDS.clear()
    shelf.insert({"name": "ann", "age": 20, "score": 70})
    with pytest.raises(ValueError):
        shelf.insert({"name": "ann", "age": 1, "score": 1})
