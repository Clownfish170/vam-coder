import depot
import quota
import api


def _seed(n):
    depot.ROWS.clear()
    for i in range(n):
        depot.put(f"k{i:02d}", {"name": f"n{i}", "score": i})


def test_page_size_constant():
    assert quota.PAGE_SIZE == 3


def test_page():
    _seed(7)
    assert [r["name"] for r in depot.page(0)] == ["n0", "n1", "n2"]
    assert [r["name"] for r in depot.page(1)] == ["n3", "n4", "n5"]
    assert [r["name"] for r in depot.page(2)] == ["n6"]


def test_page_beyond():
    _seed(2)
    assert depot.page(5) == []


def test_count_regression():
    _seed(3)
    assert api.count("name", "n1") == 1
