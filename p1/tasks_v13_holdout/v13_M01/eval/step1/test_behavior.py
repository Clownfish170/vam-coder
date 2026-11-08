import roll


def test_join_names_comma():
    assert roll.join_names(roll.ROWS) == "ada, bob"


def test_teams_regression():
    assert roll.teams(roll.ROWS) == ["x", "y"]
