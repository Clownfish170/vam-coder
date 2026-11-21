import jobsched
import report


def test_name_tiebreak():
    jobsched.QUEUE.clear()
    jobsched.push("zeta", 5)
    jobsched.push("alpha", 5)
    assert jobsched.pop() == "alpha"
    assert jobsched.pop() == "zeta"


def test_preview_follows_rule():
    jobsched.QUEUE.clear()
    jobsched.push("zeta", 5)
    jobsched.push("alpha", 5)
    assert report.preview() == "alpha"


def test_summary_follows_rule():
    jobsched.QUEUE.clear()
    jobsched.push("zeta", 5)
    jobsched.push("alpha", 5)
    assert report.summary() == ["alpha@5", "zeta@5"]
