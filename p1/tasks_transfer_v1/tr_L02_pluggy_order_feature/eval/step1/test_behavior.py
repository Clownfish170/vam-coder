from pluggy import PluginManager

def test_order_method_exists():
    pm = PluginManager("x")
    assert hasattr(pm, "get_hook_call_order")
    assert pm.get_hook_call_order() == []
