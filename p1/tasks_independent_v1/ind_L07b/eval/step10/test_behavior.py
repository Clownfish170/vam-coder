import quota
import depot
import api


def test_page_size_revised():
    assert quota.PAGE_SIZE == 2
    depot.ROWS.clear()
    for i in range(5):
        depot.put(f"k{i}", {"name": f"n{i}"})
    assert [r["name"] for r in depot.page(0)] == ["n0", "n1"]
    assert [r["name"] for r in depot.page(1)] == ["n2", "n3"]


def test_full_chain():
    depot.ROWS.clear()
    depot.put("a", {"name": "ann", "team": "red", "score": 70})
    depot.put("b", {"name": "bob", "team": "red", "score": 90})
    depot.put("c", {"name": "cyd", "team": "blue", "score": 40})
    assert depot.get("a")["score"] == 70
    assert [r["name"] for r in depot.where("team", "red")] == ["ann", "bob"]
    assert api.count("team", "red") == 2
    assert [r["name"] for r in depot.top("score", 2)] == ["bob", "ann"]
    assert len(depot.page(0)) == 2
