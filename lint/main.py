"""
Main file.

Contains run_linters and run_validators


"""
from lint.linters.lint_factory import LintFactory
from lint.validators.validation_factory import ValidatorFactory


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
    for file_type, file_list in list(files.items()):
        linter = LintFactory.get_linter(file_type)
        if linter is not None:
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
    for file_type, lint_data in list(new_data.items()):
        #TODO: What to do if old data doesn't have this filetype?
        old_lint_data = old_data.get(file_type, {})
        validator = ValidatorFactory.get_validator(file_type)
        if validator is not None:
            validation_data[validator.name] = validator.run(lint_data, old_lint_data)
    return validation_data