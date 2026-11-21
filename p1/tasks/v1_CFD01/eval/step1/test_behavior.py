import tax, invoice


def test_rate():
    assert tax.tax_rate() == 0.5


def test_grand():
    assert invoice.grand_total(1000) == 1500
