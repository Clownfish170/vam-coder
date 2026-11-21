import tempfile
from pathlib import Path
import pytest
from dotenv import DotEnv

def test_default_ignores_bad_lines():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / ".env"
        p.write_text("GOOD=1\nNOT A VALID LINE\n", encoding="utf-8")
        de = DotEnv(str(p), strict=False)
        _ = de.dict()

def test_strict_true_raises_on_bad_lines():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / ".env"
        p.write_text("GOOD=1\nNOT A VALID LINE\n", encoding="utf-8")
        with pytest.raises(Exception):
            de = DotEnv(str(p), strict=True)
            _ = de.dict()
