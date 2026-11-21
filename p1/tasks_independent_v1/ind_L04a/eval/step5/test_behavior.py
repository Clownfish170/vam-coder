import journal


def test_history_all():
    journal.JOURNAL.clear()
    journal.record(("append", "a"))
    journal.record(("undo", "a"))
    assert journal.history() == [("append", "a"), ("undo", "a")]


def test_history_kind():
    journal.JOURNAL.clear()
    journal.record(("append", "a"))
    journal.record(("undo", "a"))
    assert journal.history("undo") == [("undo", "a")]


def test_size_regression():
    journal.JOURNAL.clear()
    journal.record(("append", "a"))
    assert journal.size() == 1
