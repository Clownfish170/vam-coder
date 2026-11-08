import pytest
import rules
import shelf


def _seed():
    shelf.RECORDS.clear()
    shelf.insert({"name": "ann", "age": 20, "score": 70})
    shelf.insert({"name": "bob", "age": 15, "score": 90})
    shelf.insert({"name": "cyd", "age": 30, "score": 40})


def test_min_age_constant():
    assert rules.MIN_AGE == 18


def test_adults():
    _seed()
    assert [r["name"] for r in shelf.adults()] == ["ann", "cyd"]


def test_score_bound_regression():
    shelf.RECORDS.clear()
    with pytest.raises(ValueError):
        shelf.insert({"name": "a", "age": 1, "score": 101})
