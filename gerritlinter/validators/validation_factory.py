"""
Validator factory.

Given an extension, will return a
registered Linter.
"""
from pylint_validator import PylintValidator, DEFAULT_CHECKERS

class ValidatorException(Exception):
    pass

class ValidatorFactory(object):
    PLUGINS = [PylintValidator(DEFAULT_CHECKERS)]

    @staticmethod
    def get_validator(ext):
        """
        Gets a Linter for the given extension.

        :param ext:
        :return:
        """
        for plugin in ValidatorFactory.PLUGINS:
            if ext in plugin.EXTS:
                return plugin

    @staticmethod
    def register_validator(validator):
        """
        Register a Linter class for file verification.

        :param linter:
        :return:
        """
        if hasattr(validator, "EXTS") and hasattr(validator, "run"):
            ValidatorFactory.PLUGINS.append(validator)
        else:
            raise ValidatorException("Validator does not have 'run' method or EXTS variable!")
