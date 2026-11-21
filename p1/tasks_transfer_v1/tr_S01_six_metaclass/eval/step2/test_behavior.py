import six

def test_multi_base():
    class Base:
        pass
    class D(six.with_metaclass(type, Base, object)):
        pass
    assert isinstance(D(), Base)
    assert isinstance(D(), object)
