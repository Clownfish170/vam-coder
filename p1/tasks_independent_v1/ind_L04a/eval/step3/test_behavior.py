import doc
import journal


def test_append_records():
    doc.LINES.clear()
    journal.JOURNAL.clear()
    doc.append_line("hello")
    assert doc.LINES == ["hello"]
    assert journal.JOURNAL == [("append", "hello")]


def test_append_multiple():
    doc.LINES.clear()
    journal.JOURNAL.clear()
    doc.append_line("a")
    doc.append_line("b")
    assert journal.size() == 2


def test_remove_regression():
    doc.LINES.clear()
    doc.LINES.extend(["a", "b"])
    assert doc.remove_last() == "b"
