from pluggy._result import Result

def test_exception_not_ok():
    r = Result(result=None, exception=ValueError("x"))
    assert r.ok is False

def test_none_result_ok():
    r = Result(result=None, exception=None)
    assert r.ok is True
