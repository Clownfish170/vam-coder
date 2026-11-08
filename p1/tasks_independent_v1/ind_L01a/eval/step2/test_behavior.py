import pytest
import jobsched


def test_reject_below_min():
    jobsched.QUEUE.clear()
    with pytest.raises(ValueError):
        jobsched.push("x", -1)


def test_accept_min():
    jobsched.QUEUE.clear()
    jobsched.push("a", 0)
    assert jobsched.pop() == "a"


def test_order_regression():
    jobsched.QUEUE.clear()
    jobsched.push("a", 1)
    jobsched.push("b", 5)
    assert jobsched.pop() == "b"
    assert jobsched.pop() == "a"
