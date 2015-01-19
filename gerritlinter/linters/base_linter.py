"""
Base class for linters.

"""
from abc import abstractmethod


class Linter(object):
    EXTS = []

    @abstractmethod
    def run(self, file_list):
        """
        Override this method!
        Needs to return a valid data set to match your
        Validator class!

        :param file_list:
        :return:
        """
        pass


class NullLinter(Linter):
    """
    Default linter for unsupported file types.
    """

    def run(self, file_list):
        """
        Do nothing! Return an empty data set.

        :param file_list:
        :return:
        """
        return {}