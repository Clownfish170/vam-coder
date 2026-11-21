import blocks


def test_base_plain():
    assert blocks.Block().plain() == ""


def test_para_plain_inherited():
    assert blocks.Para("  hi  ").plain() == "hi"


def test_quote_plain_inherited():
    assert blocks.Quote("  x ").plain() == ">   x"


def test_envelope_regression():
    assert blocks.Para("hi").envelope() == "<para>hi</para>"
