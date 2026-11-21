import depot


def _seed():
    depot.ROWS.clear()
    depot.put("b", {"name": "bob", "team": "red"})
    depot.put("a", {"name": "ann", "team": "red"})
    depot.put("c", {"name": "cyd", "team": "blue"})


def test_where():
    _seed()
    out = depot.where("team", "red")
    assert [r["name"] for r in out] == ["ann", "bob"]


def test_where_none():
    _seed()
    assert depot.where("team", "green") == []


def test_empty_key_regression():
    import pytest
    depot.ROWS.clear()
    with pytest.raises(ValueError):
        depot.put("", {"name": "x"})
