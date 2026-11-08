import pytest
import depot


def test_empty_key_rejected():
    depot.ROWS.clear()
    with pytest.raises(ValueError):
        depot.put("", {"name": "x"})


def test_key_ok():
    depot.ROWS.clear()
    depot.put("k", {"name": "x"})
    assert "k" in depot.ROWS


def test_get_regression():
    depot.ROWS.clear()
    depot.put("k", {"name": "x"})
    assert depot.get("k")["name"] == "x"
