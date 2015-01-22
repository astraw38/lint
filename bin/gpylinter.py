#!/usr/bin/python
"""
Command-line script to automatically run lint.

"""
import os
import argparse
from git import Repo
from lint.main import run_linters, run_validators
from lint.utils.general import dump_to_console, post_to_gerrit, sort_by_type, cd_ctx
from lint.utils.git_utils import checkout, get_files_changed


def main(review_id, repository, branch="development", user='admin', gerrit=None):
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
    raw_file_list = get_files_changed(repository=repository, review_id=review_id)
    checkout(repository=repository, target=branch)

    files = sort_by_type(raw_file_list)
    old_data = run_linters(files)

    commit_id = checkout(repository=repository, target=review_id)

    new_data = run_linters(files)
    dump_to_console(new_data['py'])

    validations = run_validators(new_data, old_data)

    # Get the lowest score from all validators.
    final_score = min(validations.values(), key=lambda x: x[0])
    comment = ""
    for name, validation in validations.items():
        score, message = validation
        # Each validator should return it's own specialized comment
        # Ex: 'Passed <name> Validation!\n', or 'Failed <name> Validation!\n<reasons/data>\n'
        if message[-1:] != "\n":
            message += "\n"
        comment += message

    exit_code = 1 if final_score < 0 else 0

    post_to_gerrit(commit_id, score=final_score, message=comment, user=user, gerrit=gerrit)
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
                        help="Specify location of the git repository. Defaults to current directory.",
                        action="store",
                        default=os.path.curdir)
    parser.add_argument("-u", "--user",
                        help="Specify ssh user. Defaults to $USER.",
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
