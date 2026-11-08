import jobsched
import report


def test_summary():
    jobsched.QUEUE.clear()
    jobsched.push("a", 1)
    jobsched.push("b", 5)
    assert report.summary() == ["b@5", "a@1"]


def test_summary_empty():
    jobsched.QUEUE.clear()
    assert report.summary() == []


def test_take_regression():
    jobsched.QUEUE.clear()
    jobsched.push("x", 2)
    jobsched.push("y", 4)
    assert jobsched.take(1) == ["y"]
