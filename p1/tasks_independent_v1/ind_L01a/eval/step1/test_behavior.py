import jobsched


def test_priority_order():
    jobsched.QUEUE.clear()
    jobsched.push("a", 1)
    jobsched.push("b", 5)
    jobsched.push("c", 3)
    assert jobsched.pop() == "b"
    assert jobsched.pop() == "c"
    assert jobsched.pop() == "a"


def test_fifo_within_priority():
    jobsched.QUEUE.clear()
    jobsched.push("z", 4)
    jobsched.push("y", 4)
    assert jobsched.pop() == "z"
    assert jobsched.pop() == "y"


def test_empty():
    jobsched.QUEUE.clear()
    assert jobsched.pop() is None
