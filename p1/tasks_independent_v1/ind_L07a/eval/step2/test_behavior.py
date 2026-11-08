import pytest
import shelf


def _seed():
    shelf.RECORDS.clear()
    shelf.insert({"name": "ann", "age": 20, "score": 70})


def test_duplicate_rejected():
    _seed()
    with pytest.raises(ValueError):
        shelf.insert({"name": "ann", "age": 21, "score": 80})
    assert len(shelf.RECORDS) == 1


def test_new_name_ok():
    _seed()
    shelf.insert({"name": "bob", "age": 15, "score": 90})
    assert len(shelf.RECORDS) == 2


def test_find_regression():
    _seed()
    assert shelf.find("ann")["age"] == 20
