from ingest import load
from warehouse import commit


def test_commit_counts():
    rows = [{"id": 1, "qty": 2}, {"id": 2, "qty": 0}]
    assert commit(rows) == {"kept": 1, "rejected": 1}


def test_commit_all_rejected():
    assert commit([{"qty": 0}]) == {"kept": 0, "rejected": 1}


def test_load_regression():
    rows = [{"id": 1, "qty": 2}, {"id": 2, "qty": 0}]
    assert load(rows) == [{"id": 1, "qty": 2}]
