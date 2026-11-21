import pytest
import depot


def test_blank_name_rejected():
    depot.ROWS.clear()
    with pytest.raises(ValueError):
        depot.put("k", {"name": "   "})
    with pytest.raises(ValueError):
        depot.put("k2", {"name": ""})


def test_missing_name_still_rejected():
    depot.ROWS.clear()
    with pytest.raises(ValueError):
        depot.put("k", {"score": 1})


def test_ok_name():
    depot.ROWS.clear()
    depot.put("k", {"name": " x "})
    assert depot.get("k")["name"] == " x "


def test_top_regression():
    depot.ROWS.clear()
    depot.put("a", {"name": "ann", "score": 5})
    depot.put("b", {"name": "bob", "score": 9})
    assert [r["name"] for r in depot.top("score", 1)] == ["bob"]
