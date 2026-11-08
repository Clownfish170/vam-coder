import doc
import viewer


def test_last_line():
    doc.LINES.clear()
    doc.LINES.extend(["a", "b"])
    assert viewer.last_line() == "b"


def test_last_line_empty():
    doc.LINES.clear()
    assert viewer.last_line() is None


def test_title_regression():
    assert viewer.title() == "doc-view"


def test_append_records_regression():
    doc.LINES.clear()
    import journal
    journal.JOURNAL.clear()
    doc.append_line("z")
    assert journal.JOURNAL == [("append", "z")]
