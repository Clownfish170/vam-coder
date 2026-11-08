import export
import loader


def test_names_v2():
    assert export.names() == ["Ann", "Bo", "Cy"]


def test_ages_regression():
    assert export.ages() == [30, 25, 0]


def test_defaults_regression():
    assert "full_name" in loader.defaults()
