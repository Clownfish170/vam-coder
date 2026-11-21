import journal


def test_compact_keeps_three():
    journal.JOURNAL.clear()
    for i in range(5):
        journal.record(("append", f"l{i}"))
    kept = journal.compact()
    assert kept == ("append", "l4")
    assert journal.JOURNAL == [
        ("append", "l2"), ("append", "l3"), ("append", "l4")
    ]


def test_compact_under_three():
    journal.JOURNAL.clear()
    journal.record(("append", "a"))
    journal.record(("append", "b"))
    journal.compact()
    assert len(journal.JOURNAL) == 2


def test_compact_empty_regression():
    journal.JOURNAL.clear()
    assert journal.compact() is None
