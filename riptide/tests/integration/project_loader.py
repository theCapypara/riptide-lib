"""Loads projects for integration tests"""
import inspect
import os
import shutil
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import NamedTuple, Generator, List, ContextManager
from unittest import mock

from riptide.config.document.config import Config
from riptide.config.document.project import Project
from riptide.config.loader import load_config
from riptide.engine.abstract import AbstractEngine
from riptide.tests.helpers import get_fixture_paths, get_fixture_path
from riptide.tests.integration.engine.engine_loader import load_engines
from riptide.tests.integration.engine.tester_for_engine import AbstractEngineTester


class ProjectLoadResult(NamedTuple):
    project_file_name: str
    config: Config  # with project
    engine_name: str
    engine: AbstractEngine
    engine_tester: AbstractEngineTester
    src: str
    # Temporary directory to store all files in, project is stored here
    temp_dir: str
    # Temporary ~/.config/riptide-like directory
    temp_system_dir: str


def load(testsuite, project_file_names: List[str], srcs: List[str]) -> Generator[ContextManager[ProjectLoadResult], None, None]:
    """
    Generator that returns context managers

    Loads the project files with the given names (no path, just names in tests/fixtures/project) for each engine, for each entry in srcs,
    sets the project name to (name of the calling method or name)--(project_file_names)--(current engine)--(current src)
    sets the src to each entry in srcs
    creates a system config for each engine and places the project in it

    yields for each test_project_file_name x srcs entry:
        ContextManager[ProjectLoadResult]

    Cleans up (=asks EngineTester to clean up and make sure it's cleaned up) after each test

    Repositories (riptide.config.loader.repositories.collect) are mocked and set to the fixtures directory.
    riptide.config.files.user_config_dir() is mocked and set to a temporary directory.

    The context manager starts a sub test with the appropriate values

    USAGE:
        for project_ctx in load(...):
            with project_ctx as loaded:
                print(loaded.project_file_name)
    """
    calframe = inspect.getouterframes(inspect.currentframe(), 2)
    caller_name = calframe[1][3]

    with mock.patch("riptide.config.loader.repositories.collect", return_value=[get_fixture_paths()]):
        for (engine_name, engine, engine_tester) in load_engines():
            for src in srcs:
                for project_name in project_file_names:
                    # Create temporary config directory
                    with TemporaryDirectory() as config_directory:
                        with mock.patch("riptide.config.files.user_config_dir", return_value=config_directory):
                            # Copy system config file
                            shutil.copy2(get_fixture_path('config' + os.sep + 'valid.yml'), os.path.join(config_directory, 'config.yml'))
                            # Create temporary project directory
                            with TemporaryDirectory() as project_directory:
                                # Copy project file
                                shutil.copy2(get_fixture_path('project' + os.sep + project_name), os.path.join(project_directory, 'riptide.yml'))

                                name = (caller_name + '--' + project_name + '--' + engine_name + '--' + src)

                                @contextmanager
                                def ctx_manager() -> ContextManager[ProjectLoadResult]:
                                    # replace dots with _, PyCharm seems to have parsing issues with .
                                    with testsuite.subTest(project=project_name.replace('.', '_'), src=src.replace('.', '_'), engine=engine_name):
                                        old_dir = os.getcwd()
                                        try:
                                            os.chdir(project_directory)
                                            # LOAD
                                            system_config = load_config(update_repositories=False)
                                            # Sanity assertions / first function checks
                                            assert isinstance(system_config, Config)
                                            assert "project" in system_config
                                            assert isinstance(system_config["project"], Project)
                                            # set engine name
                                            system_config["engine"] = engine_name
                                            # set project src
                                            system_config["project"]["src"] = src
                                            # set project name
                                            system_config["project"]["name"] = name

                                            yield ProjectLoadResult(
                                                project_file_name=project_name,
                                                config=system_config,
                                                src=src,
                                                engine_name=engine_name,
                                                engine=engine,
                                                engine_tester=engine_tester,
                                                temp_dir=project_directory,
                                                temp_system_dir=config_directory
                                            )
                                        finally:
                                            os.chdir(old_dir)
                                            engine_tester.reset(engine)

                                yield ctx_manager()
