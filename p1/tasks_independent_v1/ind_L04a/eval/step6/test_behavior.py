import doc
import journal


def test_undo_last():
    doc.LINES.clear()
    journal.JOURNAL.clear()
    doc.append_line("a")
    doc.append_line("b")
    assert doc.undo_last() == "b"
    assert doc.LINES == ["a"]
    assert journal.JOURNAL == [("append", "a")]
    assert doc.REDO_STACK == ["b"]


def test_undo_nothing():
    doc.LINES.clear()
    journal.JOURNAL.clear()
    assert doc.undo_last() is None


def test_last_line_regression():
    doc.LINES.clear()
    doc.LINES.extend(["x", "y"])
    import viewer
    assert viewer.last_line() == "y"
