"""
Git-related utilities.
"""


def checkout(repository, target):
    """
    Check out target into the current directory.
    Target can be a branch, review Id, or commit.

    :param repository: Current git repository.
    :param target: Review ID, commit, branch.
    :return: Return the most recent commit ID (top of the git log).
    """
    # git fetch <remote> refs/changes/<review_id>
    #git checkout FETCH_HEAD
    repository.git.fetch([next(iter(repository.remotes)), target])
    repository.git.checkout("FETCH_HEAD")
    return repository.git.rev_parse(["--short", "HEAD"]).encode('ascii', 'ignore')


def get_files_changed(repository, review_id):
    """
    Get a list of files changed compared to the given review.
    Compares against current directory.

    :param repository: Git repository. Used to get remote.
      - By default uses first remote in list.
    :param review_id: Gerrit review ID.
    :return: List of file paths relative to current directory.
    """
    repository.git.fetch([next(iter(repository.remotes)), review_id])
    files_changed = repository.git.diff_tree(["--no-commit-id",
                                              "--name-only",
                                              "-r",
                                              "FETCH_HEAD"]).splitlines()
    print("Found {} files changed".format(len(files_changed)))
    return files_changed
