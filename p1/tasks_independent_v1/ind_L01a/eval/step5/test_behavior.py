import jobsched
import report


def test_take_batch():
    jobsched.QUEUE.clear()
    jobsched.push("a", 1)
    jobsched.push("b", 5)
    jobsched.push("c", 3)
    assert jobsched.take(2) == ["b", "c"]
    assert len(jobsched.QUEUE) == 1


def test_take_more_than_size():
    jobsched.QUEUE.clear()
    jobsched.push("a", 2)
    assert jobsched.take(5) == ["a"]
    assert jobsched.QUEUE == []


def test_preview_regression():
    jobsched.QUEUE.clear()
    jobsched.push("a", 1)
    jobsched.push("b", 5)
    assert report.preview() == "b"
