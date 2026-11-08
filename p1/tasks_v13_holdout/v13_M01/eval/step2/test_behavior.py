import pretty
import roll


def test_pad_right():
    assert pretty.pad("ab", 5) == "ab   "
    assert pretty.pad("ab", 2) == "ab"


def test_join_regression():
    assert roll.join_names(roll.ROWS) == "ada, bob"
