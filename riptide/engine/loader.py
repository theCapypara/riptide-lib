import pkg_resources

from riptide.plugin.loader import load_plugins

ENGINE_ENTRYPOINT_KEY = 'riptide.engine'


def load_engine(engine_name):
    """Load the engine by the given name. Propagates loaded engine to all projects."""
    # Look up package entrypoints for engines
    engines = {
        entry_point.name:
            entry_point.load() for entry_point in pkg_resources.iter_entry_points(ENGINE_ENTRYPOINT_KEY)
    }
    if engine_name in engines:
        instance = engines[engine_name]()
        for plugin in load_plugins().values():
            plugin.after_load_engine(instance)
        return instance
    raise NotImplementedError(f"Unknown Engine {engine_name}")
