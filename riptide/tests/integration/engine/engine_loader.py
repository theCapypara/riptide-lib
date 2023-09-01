from typing import Generator, Tuple

from importlib.metadata import entry_points

from riptide.engine.abstract import AbstractEngine
from riptide.engine.loader import ENGINE_ENTRYPOINT_KEY
from riptide.tests.integration.engine.tester_for_engine import AbstractEngineTester

ENGINE_TESTER_ENTRYPOINT_KEY = 'riptide.engine.tests'


def load_engines() -> Generator[Tuple[str, AbstractEngine, AbstractEngineTester], None, None]:
    """Generator that returns tuples of (name, engine, engine_tester)"""

    # Collect testers
    engine_testers = {
        entry_point.name:
            entry_point.load() for entry_point in entry_points(group=ENGINE_TESTER_ENTRYPOINT_KEY)
    }

    # Iterate engines
    for engine_entry_point in entry_points(group=ENGINE_ENTRYPOINT_KEY):
        if engine_entry_point.name not in engine_testers:
            print(f"WARNING: No engine tester found for {engine_entry_point.name}. Was not tested.")
            continue
        if not issubclass(engine_testers[engine_entry_point.name], AbstractEngineTester):
            print(f"WARNING: Engine tester for {engine_entry_point.name} was not instance of AbstractEngineTester. Was not tested.")
            continue
        engine = engine_entry_point.load()
        if not issubclass(engine, AbstractEngine):
            raise AssertionError(f"An engine must be an instance of AbstractEngine. {engine_entry_point.name} was not.")

        yield (engine_entry_point.name, engine(), engine_testers[engine_entry_point.name]())
