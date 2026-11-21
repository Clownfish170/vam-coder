import blocks


def test_para_envelope():
    assert blocks.Para("hi").envelope() == "<para>hi</para>"


def test_image_envelope():
    assert blocks.Image("a.png").envelope() == "<image>a.png</image>"


def test_base_envelope():
    assert blocks.Block().envelope() == "<block></block>"


def test_kind_regression():
    assert blocks.Image("x").kind() == "image"
