import desk
import console


def test_drain():
    desk.BUCKETS.clear()
    desk.admit("a", 3)
    desk.admit("b", 3)
    desk.admit("c", 3)
    assert desk.drain(3, 2) == ["a", "b"]
    assert desk.count(3) == 1


def test_drain_missing_level():
    desk.BUCKETS.clear()
    assert desk.drain(8, 3) == []


def test_board_regression():
    desk.BUCKETS.clear()
    desk.admit("a", 1)
    assert console.board() == {1: 1}
