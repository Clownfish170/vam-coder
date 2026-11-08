import blocks


def test_quote():
    q = blocks.Quote("note")
    assert q.render() == "> note"
    assert q.kind() == "quote"


def test_envelope_regression():
    assert blocks.Para("hi").envelope() == "<para>hi</para>"


def test_image_regression():
    assert blocks.Image("a.png").kind() == "image"
