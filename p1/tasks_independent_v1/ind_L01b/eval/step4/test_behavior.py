import desk
import console


def test_board():
    desk.BUCKETS.clear()
    desk.admit("a", 2)
    desk.admit("b", 2)
    desk.admit("c", 5)
    assert console.board() == {2: 2, 5: 1}


def test_board_empty():
    desk.BUCKETS.clear()
    assert console.board() == {}


def test_show_regression():
    assert console.show("j1") == "job=j1"
