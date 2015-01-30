"""
Validation class.

Combines a set of validations for pylint results.
"""
from .base_validator import Validator
PYLINT_SCORE_THRESHOLD = 9


class PylintValidator(Validator):
    """
    Encompasses pylint score validators.

    Each Validator should follow this pattern:
     validator(new_data, old_data, strict=False/True):
       return (success (bool), score (int), message(str))

    Allows for easier management of what should cause a -1 Score and
    the related gerrit comment.
    """
    EXTS = ['py']

    def __init__(self, checkers=None):
        """
        Initialize the class with given checkers.
        """
        if checkers is None:
            checkers = []
        self.name = "PylintValidator"
        self.checkers = checkers
        self.default_score = 1
        self.default_message = "Passed pylint with an average score of {}!"

    def run(self, new_pylint_data, old_pylint_data):
        """
        Run the new pylint data through given all current checkers,
        including comparisons to old pylint data.

        """
        for validator in self.checkers:
            success, score, message = validator(new_pylint_data, old_pylint_data)
            if not success:
                return score, message

        message = self.default_message.format(new_pylint_data['average'])
        return self.default_score, message


def no_new_errors(new_data, old_data, strict=False):
    """
    Pylint Validator that will fail any review if there are
    new Pylint errors in it (Pylint message starts with 'E:')

    :param new_data:
    :param old_data:
    :return:
    """
    success = True
    score = 0
    message = ''
    if new_data['errors'] > old_data['errors']:
        success = False
        message = "Failed, More errors than prior runs!({} > {})\n" \
                  "Average Score: {}".format(new_data['errors'],
                                             old_data['errors'],
                                             new_data['average'])
        score = -1

    return success, score, message


def above_score_threshold(new_data, old_data, strict=False, threshold=PYLINT_SCORE_THRESHOLD):
    """
    Verifies that the pylint score is above a given threshold.

    :param new_data:
    :param old_data:
    :return:
    """
    success = True
    score = 0
    message = ''
    if strict:
        for fscore, fname in new_data['scores']:
            if fscore < threshold:
                success = False
                score = -1
                message += "File {} score ({}) below threshold {}\n".format(fname, fscore, threshold)

        return success, score, message

    else:
        if new_data['average'] < threshold:
            success = False
            message = "Failed! Average pylint score ({})" \
                      " below threshold (9)!".format(new_data['average'])
            score = -1

    return success, score, message


DEFAULT_CHECKERS = [no_new_errors, above_score_threshold]
