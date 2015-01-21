"""
Base class for Validators.

"""
from abc import abstractmethod


class Validator(object):
    EXTS = []

    @abstractmethod
    def run(self, new_data, old_data):
        """
        Override this method!
        Needs to return a tuple:
        (success, score, gerrit_comment)

        :param new_data:
        :param old_data:
        :return:
        """
        pass


class NullValidator(Validator):
    """
    Default Validator for unsupported file types.
    """
    def __init__(self):
        """
        Null validator.
        :return:
        """
        self.name = "NullValidator"

    def run(self, new_data, old_data):
        """
        Do nothing! Return an empty data set.

        :param new_data:
        :param old_data: 
        :return:
        """
        return 1, "No Validation specified for this filetype."