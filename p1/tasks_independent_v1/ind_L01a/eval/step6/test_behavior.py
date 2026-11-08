import pytest
import jobsched
import policy


def test_cap_constant():
    assert policy.CAP == 3


def test_full_queue():
    jobsched.QUEUE.clear()
    for i in range(3):
        jobsched.push(f"j{i}", 2)
    with pytest.raises(ValueError):
        jobsched.push("extra", 2)


def test_take_regression():
    jobsched.QUEUE.clear()
    jobsched.push("a", 1)
    jobsched.push("b", 5)
    assert jobsched.take(2) == ["b", "a"]
