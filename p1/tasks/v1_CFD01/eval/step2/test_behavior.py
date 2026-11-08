import invoice


def test_net():
    assert invoice.net_total(1500) == 1000


def test_grand_still():
    assert invoice.grand_total(1500) == 2250
