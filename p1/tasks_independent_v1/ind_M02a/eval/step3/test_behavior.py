import export


def test_ages():
    assert export.ages() == [30, 25, 0]


def test_names_regression():
    assert export.names() == ["Ann", "Bo", "Cy"]
