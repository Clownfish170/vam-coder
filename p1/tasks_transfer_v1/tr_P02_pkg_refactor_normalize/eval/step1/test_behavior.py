from packaging.utils import canonicalize_version
import packaging.utils as u

def test_helper_exists():
    assert hasattr(u, "_normalize_version")
    assert u._normalize_version("  ABC  ") == "abc"

def test_canonicalize_still_works():
    out = canonicalize_version("1.0.post1")
    assert isinstance(out, str) and out
