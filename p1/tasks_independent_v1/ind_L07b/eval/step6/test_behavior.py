import pytest
import depot


def test_missing_name():
    depot.ROWS.clear()
    with pytest.raises(ValueError):
        depot.put("k", {"score": 10})


def test_name_present():
    depot.ROWS.clear()
    depot.put("k", {"name": "x", "score": 10})
    assert depot.get("k")["score"] == 10


def test_page_regression():
    depot.ROWS.clear()
    for i in range(4):
        depot.put(f"k{i}", {"name": f"n{i}"})
    assert len(depot.page(1)) == 1
