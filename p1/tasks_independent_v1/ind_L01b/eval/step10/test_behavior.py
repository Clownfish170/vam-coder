import desk
import rules
import console


def test_default_now_seven():
    assert rules.DEFAULT_LEVEL == 7
    desk.BUCKETS.clear()
    desk.admit("auto")
    assert desk.count(7) == 1
    assert desk.next_job() == "auto"


def test_full_chain():
    desk.BUCKETS.clear()
    desk.admit("low", 1)
    desk.admit("high", 7)
    assert desk.next_job() == "high"
    assert desk.next_job() == "low"
    desk.admit("a", 3)
    desk.admit("b", 3)
    assert desk.drain(3, 1) == ["a"]
    assert desk.levels() == [3]
    assert console.board() == {3: 1}
