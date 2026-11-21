import conf, conf2


def test_conf():
    assert conf.apply(2) == 6


def test_conf2():
    assert conf2.apply(2) == 7
