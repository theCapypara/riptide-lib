from typing import Generator, Tuple

import pkg_resources

from riptide.engine.abstract import AbstractEngine
from riptide.engine.loader import ENGINE_ENTRYPOINT_KEY
from riptide.tests.integration.engine.tester_for_engine import AbstractEngineTester

ENGINE_TESTER_ENTRYPOINT_KEY = 'riptide.engine.tests'


def load_engines() -> Generator[Tuple[str, AbstractEngine, AbstractEngineTester], None, None]:
    """Generator that returns tuples of (name, engine, engine_tester)"""

    # Collect testers
    engine_testers = {
        entry_point.name:
            entry_point.load() for entry_point in pkg_resources.iter_entry_points(ENGINE_TESTER_ENTRYPOINT_KEY)
    }

    # Iterate engines
    for engine_entry_point in pkg_resources.iter_entry_points(ENGINE_ENTRYPOINT_KEY):
        if engine_entry_point.name not in engine_testers:
            print("WARNING: No engine tester found for %s. Was not tested." % engine_entry_point.name)
            continue
        if not issubclass(engine_testers[engine_entry_point.name], AbstractEngineTester):
            print("WARNING: Engine tester for %s was not instance of AbstractEngineTester. Was not tested." % engine_entry_point.name)
            continue
        engine = engine_entry_point.load()
        if not issubclass(engine, AbstractEngine):
            raise AssertionError("An engine must be an instance of AbstractEngine. %s was not." % engine_entry_point.name)

        yield (engine_entry_point.name, engine(), engine_testers[engine_entry_point.name]())
