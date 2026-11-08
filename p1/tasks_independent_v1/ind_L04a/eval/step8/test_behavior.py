import journal


def test_compact():
    journal.JOURNAL.clear()
    journal.record(("append", "a"))
    journal.record(("append", "b"))
    journal.record(("undo", "b"))
    kept = journal.compact()
    assert kept == ("undo", "b")
    assert journal.JOURNAL == [("undo", "b")]


def test_compact_empty():
    journal.JOURNAL.clear()
    assert journal.compact() is None


def test_history_regression():
    journal.JOURNAL.clear()
    journal.record(("append", "a"))
    assert journal.history("append") == [("append", "a")]
