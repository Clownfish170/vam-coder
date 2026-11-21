from pluggy import PluginManager

def test_clear_method():
    pm = PluginManager("y")
    assert hasattr(pm, "get_hook_call_order")
    assert hasattr(pm, "clear_hook_call_order")
    pm.clear_hook_call_order()
    assert pm.get_hook_call_order() == []
