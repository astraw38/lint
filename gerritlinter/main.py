"""
Test file.
"""
from utils.general import sort_by_type, post_to_gerrit, dump_to_console
from utils.git_utils import checkout, get_files_changed
from gerritlinter.linters.lint_factory import LintFactory
from gerritlinter.validators.validation_factory import ValidatorFactory


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
    raw_file_list = get_files_changed(repository=repository, review_id=review_id)
    checkout(repository=repository, target=branch)

    files = sort_by_type(raw_file_list)
    old_data = run_linters(files)

    commit_id = checkout(repository=repository, target=review_id)

    new_data = run_linters(files)

    validations = run_validators(new_data, old_data)

    # Get the lowest score from all validators.
    final_score = min(validations.values(), key=lambda x: x[0])
    comment = ""
    for name, validation in validations:
        score, message = validation
        # Each validator should return it's own specialized comment
        # Ex: 'Passed <name> Validation!\n', or 'Failed <name> Validation!\n<reasons/data>\n'
        if message[-1:] != "\n":
            message += "\n"
        comment += message

    exit_code = 1 if final_score < 0 else 0

    post_to_gerrit(commit_id, score=final_score, message=comment, user=user, gerrit=gerrit)
    exit(exit_code)


def run_linters(files):
    """
    Run through file list, and try to find a linter
    that matches the given file type.

    If it finds a linter, it will run it, and store the
    resulting data in a dictionary (keyed to file_type).

    :param files:
    :return: {file_extension: lint_data}
    """
    data = {}
    for file_type, file_list in files.items():
        linter = LintFactory.get_linter(file_type)
        data[file_type] = linter.run(file_list)
    return data


def run_validators(new_data, old_data):
    """
    Run through all matching validators.

    :param new_data: New lint data.
    :param old_data: Old lint data (before review)
    :return:
    """
    #{'validator_name': (success, score, message)}
    validation_data = {}
    for file_type, lint_data in new_data.items():
        #TODO: What to do if old data doesn't have this filetype?
        old_lint_data = old_data.get(file_type, {})
        validator = ValidatorFactory.get_validator(file_type)
        validation_data[validator.name] = validator.run(lint_data, old_lint_data)
    return validation_data