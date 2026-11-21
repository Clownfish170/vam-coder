import doc
import journal


def test_redo():
    doc.LINES.clear()
    journal.JOURNAL.clear()
    doc.append_line("a")
    doc.undo_last()
    assert doc.redo_last() == "a"
    assert doc.LINES == ["a"]
    assert journal.JOURNAL == [("append", "a")]
    assert doc.REDO_STACK == []


def test_redo_empty():
    doc.LINES.clear()
    journal.JOURNAL.clear()
    assert doc.redo_last() is None


def test_undo_regression():
    doc.LINES.clear()
    journal.JOURNAL.clear()
    doc.append_line("a")
    doc.append_line("b")
    assert doc.undo_last() == "b"
    assert doc.LINES == ["a"]
