from ingest import load


def test_filters_invalid_rows():
    rows = [{"id": 1, "qty": 2}, {"id": 2, "qty": 0}, {"id": 3, "qty": -1}]
    assert load(rows) == [{"id": 1, "qty": 2}]


def test_empty_input():
    assert load([]) == []
