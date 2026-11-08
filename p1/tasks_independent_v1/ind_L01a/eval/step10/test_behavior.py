import pytest
import jobsched
import policy
import report


def test_min_prio_updated():
    assert policy.MIN_PRIO == 2
    jobsched.QUEUE.clear()
    with pytest.raises(ValueError):
        jobsched.push("x", 1)
    jobsched.push("y", 2)
    assert jobsched.pop() == "y"


def test_full_chain():
    jobsched.QUEUE.clear()
    jobsched.push("beta", 4)
    jobsched.push("alpha", 4)
    assert report.preview() == "alpha"
    assert report.summary() == ["alpha@4", "beta@4"]
    assert jobsched.bump("beta", 9) is True
    assert jobsched.take(2) == ["beta", "alpha"]
    assert policy.CAP == 3
