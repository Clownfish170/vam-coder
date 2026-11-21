import tables


def test_lookup3():
    assert tables.lookup(3) == 'c'


def test_unknown():
    assert tables.lookup(99) == '?'
