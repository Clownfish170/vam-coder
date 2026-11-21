import api
import depot


def _seed():
    depot.ROWS.clear()
    depot.put("b", {"name": "bob", "team": "red"})
    depot.put("a", {"name": "ann", "team": "red"})
    depot.put("c", {"name": "cyd", "team": "blue"})


def test_count():
    _seed()
    assert api.count("team", "red") == 2


def test_count_zero():
    _seed()
    assert api.count("team", "green") == 0


def test_ping_regression():
    assert api.ping() == "pong"


def test_where_regression():
    _seed()
    assert [r["name"] for r in depot.where("team", "blue")] == ["cyd"]
