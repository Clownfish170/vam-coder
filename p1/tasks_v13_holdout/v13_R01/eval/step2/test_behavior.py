import metrics_store as ms
from reporting import summarize


def test_order_and_duplicates_kept():
    rows = [
        {"group": "x", "value": 1},
        {"group": "x", "value": 2},
        {"group": "x", "value": 1},
        {"group": "y", "value": 5},
    ]
    assert summarize(rows) == {"x": [1, 2, 1], "y": [5]}


def test_store_regression():
    ms.put("reg_c", 3)
    assert ms.HISTORY["reg_c"] == [3]
