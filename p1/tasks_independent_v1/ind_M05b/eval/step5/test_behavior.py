import blocks


def test_heading():
    h = blocks.Heading("Title", 2)
    assert h.render() == "2. Title"
    assert h.kind() == "para"
    assert isinstance(h, blocks.Para)


def test_heading_default_level():
    assert blocks.Heading("T").render() == "1. T"


def test_plain_regression():
    assert blocks.Para("  hi  ").plain() == "hi"
