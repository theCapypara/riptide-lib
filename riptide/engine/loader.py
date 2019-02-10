import pkg_resources

DB_DRIVER_ENTRYPOINT_KEY = 'riptide.engine'


def load_engine(engine_name):
    """Load the engine by the given name"""
    # Look up package entrypoints for engines
    drivers = {
        entry_point.name:
            entry_point.load() for entry_point in pkg_resources.iter_entry_points(DB_DRIVER_ENTRYPOINT_KEY)
    }
    if engine_name in drivers:
        return drivers[engine_name]()
    raise NotImplementedError("Unknown Engine %s" % engine_name)
