import doc


def test_remove_last():
    doc.LINES.clear()
    doc.LINES.extend(["a", "b"])
    assert doc.remove_last() == "b"
    assert doc.LINES == ["a"]


def test_remove_empty():
    doc.LINES.clear()
    assert doc.remove_last() is None


def test_append_regression():
    doc.LINES.clear()
    doc.append_line("x")
    assert doc.LINES == ["x"]
