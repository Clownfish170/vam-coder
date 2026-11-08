import pytest
import jobsched


def test_bump_missing_raises():
    jobsched.QUEUE.clear()
    with pytest.raises(KeyError):
        jobsched.bump("ghost", 3)


def test_bump_found_regression():
    jobsched.QUEUE.clear()
    jobsched.push("a", 1)
    jobsched.push("b", 5)
    assert jobsched.bump("a", 9) is True
    assert jobsched.pop() == "a"


def test_name_tiebreak_regression():
    jobsched.QUEUE.clear()
    jobsched.push("zeta", 5)
    jobsched.push("alpha", 5)
    assert jobsched.pop() == "alpha"
