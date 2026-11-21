import blocks


def test_image():
    im = blocks.Image("pic.png")
    assert im.render() == "[img:pic.png]"
    assert im.kind() == "image"
    assert isinstance(im, blocks.Block)


def test_para_regression():
    p = blocks.Para("hi")
    assert p.render() == "hi"
    assert p.kind() == "para"
