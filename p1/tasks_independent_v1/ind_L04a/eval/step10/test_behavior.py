import pytest
import doc
import journal


def test_append_blank():
    doc.LINES.clear()
    journal.JOURNAL.clear()
    with pytest.raises(ValueError):
        doc.append_line("")
    with pytest.raises(ValueError):
        doc.append_line("   ")


def test_append_ok():
    doc.LINES.clear()
    journal.JOURNAL.clear()
    doc.append_line("ok")
    assert doc.LINES == ["ok"]
    assert journal.JOURNAL == [("append", "ok")]


def test_compact_regression():
    journal.JOURNAL.clear()
    for i in range(4):
        journal.record(("append", f"l{i}"))
    journal.compact()
    assert len(journal.JOURNAL) == 3
