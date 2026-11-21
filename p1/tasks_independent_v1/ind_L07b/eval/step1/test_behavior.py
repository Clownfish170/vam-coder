import depot


def _seed():
    depot.ROWS.clear()
    depot.put("a", {"name": "ann", "score": 70})
    depot.put("b", {"name": "bob", "score": 90})


def test_get():
    _seed()
    assert depot.get("b")["score"] == 90


def test_get_default():
    _seed()
    assert depot.get("zz") is None
    assert depot.get("zz", {}) == {}


def test_put_regression():
    _seed()
    assert len(depot.ROWS) == 2
