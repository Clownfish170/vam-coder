import metrics_store as ms


def test_history_appends_in_order():
    ms.put("seq_a", 1)
    ms.put("seq_a", 2)
    assert ms.HISTORY["seq_a"] == [1, 2]


def test_data_holds_latest():
    ms.put("latest_b", 9)
    assert ms.get("latest_b") == 9
