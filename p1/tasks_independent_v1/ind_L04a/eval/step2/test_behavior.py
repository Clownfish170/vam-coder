import journal


def test_size_empty():
    journal.JOURNAL.clear()
    assert journal.size() == 0


def test_size_after_record():
    journal.JOURNAL.clear()
    journal.record(("append", "a"))
    journal.record(("append", "b"))
    assert journal.size() == 2


def test_record_regression():
    journal.JOURNAL.clear()
    journal.record(("append", "a"))
    assert journal.JOURNAL == [("append", "a")]
