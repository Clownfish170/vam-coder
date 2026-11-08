import shelf
import views


def _seed():
    shelf.RECORDS.clear()
    for i, s in enumerate((10, 20, 30, 40)):
        shelf.insert({"name": f"n{i}", "age": 20, "score": s})


def test_page():
    _seed()
    assert [r["name"] for r in shelf.page(1, 2)] == ["n1", "n2"]


def test_page_beyond_end():
    _seed()
    assert [r["name"] for r in shelf.page(3, 5)] == ["n3"]


def test_top_regression():
    _seed()
    assert views.top_names(1) == ["n3"]
