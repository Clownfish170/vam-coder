import quota
import depot


def test_page_size_updated():
    assert quota.PAGE_SIZE == 5


def test_page_follows():
    depot.ROWS.clear()
    for i in range(7):
        depot.put(f"k{i:02d}", {"name": f"n{i}"})
    assert [r["name"] for r in depot.page(0)] == [
        "n0", "n1", "n2", "n3", "n4"
    ]
    assert [r["name"] for r in depot.page(1)] == ["n5", "n6"]


def test_name_constraint_regression():
    import pytest
    depot.ROWS.clear()
    with pytest.raises(ValueError):
        depot.put("k", {"score": 1})
