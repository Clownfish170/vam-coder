from pluggy._result import Result

def test_zero_result_is_ok():
    r = Result(result=0, exception=None)
    assert r.ok is True

def test_false_result_is_ok():
    r = Result(result=False, exception=None)
    assert r.ok is True
