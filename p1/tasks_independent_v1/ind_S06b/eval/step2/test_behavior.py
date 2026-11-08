import names


def test_drop_digits():
    assert names.drop_digits("a1b22") == "ab"


def test_all_digits():
    assert names.drop_digits("42") == ""


def test_slugify_regression():
    assert names.slugify("Hello World") == "hello-world"
