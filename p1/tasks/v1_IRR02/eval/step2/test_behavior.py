import importlib
import pytest


def test_scratch_gone():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module('scratch')
