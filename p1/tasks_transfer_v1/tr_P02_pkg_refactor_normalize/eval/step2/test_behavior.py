from packaging.utils import canonicalize_name, canonicalize_version
import packaging.utils as u

def test_canonicalize_name():
    assert canonicalize_name(" Foo.Bar ") == "foo-bar"

def test_normalize_used():
    assert u._normalize_version("  1.0  ") == "1.0"
    assert canonicalize_version("1.0") == "1.0"
