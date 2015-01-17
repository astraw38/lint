#!/usr/bin/python
"""
Command-line script to automatically run gerritlinter.

"""
import os
import argparse
from git import Repo
from gerritlinter.utils.general import dump_to_console, post_to_gerrit
from gerritlinter.utils.git_utils import checkout, get_files_changed
from gerritlinter.linters.pylinter import pylint
from gerritlinter.validators.pylint_validator import PylintValidator

def main(review_id, repository, branch="development", user='lunatest', gerrit=None):
    """
    Do the bulk of the work

    Exit status will be 1 if pylint fails.
    Exit status will be 0 if pylint passes.

    :param review_id: Target gerrit review ID. ex: refs/changes/99/299/3
    :param repository: Git repository.
    :param branch: Git branch to compare to.
    :param user: SSH User that can connect to gerrit and post scores.
    :param gerrit: Gerrit hostname.
    """
    checkout(repository, branch)
    file_list = get_files_changed(repository=repository, review_id=review_id)
    checkout(repository=repository, target=branch)
    print "Pre-review pylint data:"
    old_pylint_data = pylint(file_list)

    commit_id = checkout(repository=repository, target=review_id)
    print "Post-review pylint data:"
    new_pylint_data = pylint(file_list)

    validator = PylintValidator(checkers=[no_new_errors, above_score_threshold])

    score, message = validator.validate(new_pylint_data, old_pylint_data)
    exit_code = 1 if score < 0 else 0

    dump_to_console(new_pylint_data)
    post_to_gerrit(commit_id, score=score, message=message, user=user, gerrit=gerrit)
    exit(exit_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--review_id",
                        help="Review ID to compare against.",
                        action="store",
                        default=None)
    parser.add_argument("-b", "--branch",
                        help="Specify a branch to compare against.",
                        action="store",
                        default=os.environ.get('GERRIT_BRANCH', 'development'))
    parser.add_argument("-r", "--repo",
                        help="Specify location of the git repository",
                        action="store",
                        default=os.path.curdir)
    parser.add_argument("-u", "--user",
                        help="Specify ssh user",
                        action="store",
                        default=os.environ.get('USER'))
    parser.add_argument("--host",
                        help="Manually specify the Gerrit hostname. Defaults to $GERRIT_HOST",
                        default=os.environ.get('GERRIT_HOST'))

    args = parser.parse_args()

    if args.review_id is None:
        # Get the review ID from the env vars.
        review = os.environ.get('GERRIT_REFSPEC')
    else:
        # Manual specification of review ID.
        review = args.review_id
        review = "refs/changes/{}".format(review.lstrip('/'))

    print "Checking review id: {}".format(review)
    repository = Repo(args.repo)
    with cd_ctx(args.repo):
        main(review_id=review, repository=repository, branch=args.branch, user=args.user, gerrit=args.host)
