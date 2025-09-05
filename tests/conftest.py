def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.get_closest_marker("v5_2_6"):
            item.add_marker("v5")
        if item.get_closest_marker("v4_1_73"):
            item.add_marker("v4")
