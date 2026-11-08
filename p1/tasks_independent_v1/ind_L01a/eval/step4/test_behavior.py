import jobsched
import report


def test_preview():
    jobsched.QUEUE.clear()
    jobsched.push("a", 1)
    jobsched.push("b", 5)
    assert report.preview() == "b"
    assert len(jobsched.QUEUE) == 2


def test_preview_empty():
    jobsched.QUEUE.clear()
    assert report.preview() is None


def test_bump_regression():
    jobsched.QUEUE.clear()
    jobsched.push("a", 1)
    jobsched.push("b", 5)
    assert jobsched.bump("a", 9) is True
    assert jobsched.pop() == "a"
