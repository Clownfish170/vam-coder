import names


def test_spaces():
    assert names.slugify("  Hello  World ") == "hello-world"


def test_underscore_kept():
    assert names.slugify("A_B") == "a_b"


def test_simple():
    assert names.slugify("Up") == "up"
