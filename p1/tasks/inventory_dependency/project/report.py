def catalog_value(catalog):
    """Total catalog value (unrelated to stock math; control file)."""
    return sum(item.get("price", 0) * item.get("qty", 0) for item in catalog)
