import jobsched


def test_bump_found():
    jobsched.QUEUE.clear()
    jobsched.push("a", 1)
    jobsched.push("b", 5)
    assert jobsched.bump("a", 9) is True
    assert jobsched.pop() == "a"
    assert jobsched.pop() == "b"


def test_bump_missing():
    jobsched.QUEUE.clear()
    assert jobsched.bump("ghost", 3) is False


def test_reject_regression():
    import pytest
    jobsched.QUEUE.clear()
    with pytest.raises(ValueError):
        jobsched.push("x", -1)
