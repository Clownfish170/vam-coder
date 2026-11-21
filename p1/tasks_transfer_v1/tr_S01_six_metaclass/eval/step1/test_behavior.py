import six

def test_with_metaclass_basic():
    class C(six.with_metaclass(type, object)):
        pass
    assert isinstance(C(), object)

def test_is_type_subclass():
    class D(six.with_metaclass(type, object)):
        pass
    assert issubclass(D, object)
