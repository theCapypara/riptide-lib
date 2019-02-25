"""Manages the synchronization of Riptide repositories."""
import os
import shutil

from git import Repo, InvalidGitRepositoryError, NoSuchPathError, CommandError
from typing import TYPE_CHECKING

from riptide.config.files import riptide_local_repositories_path, remove_all_special_chars

if TYPE_CHECKING:
    from riptide.config.document.config import Config

TAB = '    '


def update(system_config: 'Config', update_text_func):
    """
    Update repostiories by checking remote Git state and downloading all changes.

    :param update_func: Function to execute for status updates of repository updating (one string parameter)
    :param system_config: Config that includes the repository urls.
    """
    update_text_func("Updating Riptide repositories...")
    base_dir = riptide_local_repositories_path()
    for repo_name in system_config["repos"]:
        # directory name for this repo on disk
        dir_name = os.path.join(base_dir, remove_all_special_chars(repo_name))
        try:
            repo = Repo(dir_name)
        except InvalidGitRepositoryError:
            # Delete directory and start new
            shutil.rmtree(dir_name)
            _create_new(repo_name, dir_name, update_text_func)
        except NoSuchPathError:
            # Doesn't exist yet, start new
            _create_new(repo_name, dir_name, update_text_func)
        else:
            # Update existing repositories
            try:
                _update_text(repo_name, update_text_func)
                repo.git.pull()
            except CommandError as err:
                # Git error, we can't update
                update_text_func(TAB + TAB + "Warning: Could not update: " + err.stderr.replace('\n', ' '))
    update_text_func("Done!")
    update_text_func("")


def _create_new(clone_url, repo_dir, update_text_func):
    """Create a new repository and inform update_text_func about it, returns True."""
    _update_text(clone_url, update_text_func)
    Repo.clone_from(clone_url, repo_dir)
    return True


def _update_text(repo, update_text_func):
    """
    Sends message back to update_text_func that this repo is updating.
    """
    update_text_func(TAB + "Updating '%s'..." % repo)


def collect(system_config):
    """
    Returns the absolute paths to all currently downloaded repositories.
    Removes all downloaded repos, that are not in system config.
    """
    base_dir = riptide_local_repositories_path()
    os.makedirs(base_dir, exist_ok=True)

    # Get all repos that are downloaded
    repos = set(next(os.walk(base_dir))[1])
    # Get all expected repositories, clean up the names to match the directory names
    repos_in_system_config = set(remove_all_special_chars(repo) for repo in system_config["repos"])

    # Get all repos that are downloaded, but not in the system config
    to_remove = repos - repos_in_system_config
    # remove them
    for remove in to_remove:
        shutil.rmtree(os.path.join(base_dir, remove))

    existing = repos - to_remove

    # return all repos that are downloaded and in the system config
    return [os.path.join(base_dir, dirname) for dirname in existing]

