"""Manages the synchronization of Riptide repositories."""
import os
import shutil

from git import Repo, InvalidGitRepositoryError, NoSuchPathError, CommandError
from typing import TYPE_CHECKING

from riptide.config.files import riptide_local_repositories_path, remove_all_special_chars
from riptide.util import get_riptide_version

if TYPE_CHECKING:
    from riptide.config.document.config import Config

TAB = '    '


def update(system_config: 'Config', update_text_func):
    """
    Update repostiories by checking remote Git state and downloading all changes.

    :param update_func: Function to execute for status updates of repository updating (one string parameter)
    :param system_config: Config that includes the repository urls.
    """
    base_dir = riptide_local_repositories_path()
    for repo_name in system_config["repos"]:
        # directory name for this repo on disk
        dir_name = os.path.join(base_dir, remove_all_special_chars(repo_name))
        _update_text(repo_name, update_text_func)
        try:
            repo = Repo(dir_name)
        except InvalidGitRepositoryError:
            # Delete directory and start new
            shutil.rmtree(dir_name)
            repo = Repo.clone_from(repo_name, dir_name)
        except NoSuchPathError:
            # Doesn't exist yet, start new
            repo = Repo.clone_from(repo_name, dir_name)

        # Update existing repositories
        try:
            repo.git.fetch()
            remote = repo.remotes.origin if hasattr(repo.remotes, 'origin') else repo.remotes[0]
            # Checkout either current Riptide version or master
            _checkout(repo, remote)
        except CommandError as err:
            # Git error, we can't update
            update_text_func(TAB + "Warning: Could not update: " + err.stderr.replace('\n', ' '))

        update_text_func("Done!")
        update_text_func("")

def _update_text(repo, update_text_func):
    """
    Sends message back to update_text_func that this repo is updating.
    """
    update_text_func("Updating '%s'..." % repo)


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
    repos_in_system_config = [remove_all_special_chars(repo) for repo in system_config["repos"]]

    # Get all repos that are downloaded, but not in the system config
    to_remove = repos - set(repos_in_system_config)
    # remove them
    for remove in to_remove:
        shutil.rmtree(os.path.join(base_dir, remove))

    # return all repos that are downloaded and in the system config
    return [os.path.join(base_dir, dirname) for dirname in repos_in_system_config]


def _checkout(repo, remote):
    prefix = remote.name + '/'
    ref_list = [ref.name for ref in remote.refs]
    major, minor, patch = get_riptide_version()
    if major is not None:
        if minor is not None:
            if patch is not None:
                # X.X.X
                candidate = prefix + '%s.%s.%s' % (major, minor, patch)
                if candidate in ref_list:
                    repo.git.checkout(candidate)
                    return
            # X.X
            candidate = prefix + '%s.%s' % (major, minor)
            if candidate in ref_list:
                repo.git.checkout(candidate)
                return
        # X
        candidate = prefix + str(major)
        if candidate in ref_list:
            repo.git.checkout(candidate)
            return
    # master
    candidate = prefix + 'master'
    if candidate in ref_list:
        repo.git.checkout(candidate)
        return
    # HEAD
    repo.git.checkout(prefix + 'HEAD')
