import inspect
from dotenv import DotEnv

def test_strict_param_on_dotenv():
    sig = inspect.signature(DotEnv.__init__)
    assert "strict" in sig.parameters
    assert sig.parameters["strict"].default is False

def test_construct_default():
    de = DotEnv(None)
    assert de is not None
