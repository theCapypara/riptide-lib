import pkg_resources

ENGINE_ENTRYPOINT_KEY = 'riptide.engine'


def load_engine(engine_name):
    """Load the engine by the given name"""
    # Look up package entrypoints for engines
    engines = {
        entry_point.name:
            entry_point.load() for entry_point in pkg_resources.iter_entry_points(ENGINE_ENTRYPOINT_KEY)
    }
    if engine_name in engines:
        return engines[engine_name]()
    raise NotImplementedError("Unknown Engine %s" % engine_name)
