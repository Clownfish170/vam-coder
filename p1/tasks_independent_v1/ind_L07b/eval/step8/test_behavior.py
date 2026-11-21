import depot
import quota


def _seed():
    depot.ROWS.clear()
    depot.put("a", {"name": "ann", "score": 70})
    depot.put("b", {"name": "bob", "score": 90})
    depot.put("c", {"name": "cyd", "score": 90})
    depot.put("d", {"name": "dan", "score": 40})


def test_top():
    _seed()
    assert [r["name"] for r in depot.top("score", 3)] == [
        "bob", "cyd", "ann"
    ]


def test_top_tie_by_key():
    _seed()
    assert [r["name"] for r in depot.top("score", 2)] == ["bob", "cyd"]


def test_page_regression():
    _seed()
    assert quota.PAGE_SIZE == 5
    assert len(depot.page(0)) == 4
