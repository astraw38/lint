"""
This is a custom pylinter.

It will take the active git branch and compare it to
our development branch, getting a list of files changed.

It will then pylint the original files and compare it to the
new files. Files must maintain a high pylint rating (9+ by default), and not
introduce new problems.

ver 0.1:
 - Use non-zero exit code so we get a -1 in Gerrit if it does not pass
 - Exit code of 0 will cause a +1 to be posted to the review in gerrit.

ver 0.2:
 - Use Gerrit REST API to post comments outlining what needs to
 be changed from pylint.
"""
import subprocess
import re
import os
from lint.utils.general import cd_ctx
from lint.linters.base_linter import Linter


class Pylinter(Linter):
    """
    Implements Code validation for given file type.
    """
    EXTS = ['py']

    def run(self, file_list):
        """
        Runs pylint on the list of files and return a dictionary:
         {<filename>: [list of pylint errors],
          'total': <int> - Total number of pylint messages,
          'errors': <int> - Number of pylint errors,
          'scores': (<filename>, score) - Individual score for each file.}

        :param file_list:
        :return:
        """
        data = {'total': 0,
                'errors': 0,
                'scores': []}

        for filename in file_list:
            path, fname = os.path.split(filename)
            if os.path.splitext(filename)[1] != '.py':
                #Don't run on non-python files.
                continue
            with cd_ctx(path):
                short_data = pylint_raw([fname, "--report=n", "-f", "text", '--confidence=HIGH'])
                full_data = pylint_raw([fname, "--report=y", "-f", "text", '--confidence=HIGH'])

            score_regex = re.search(r"Your code has been rated at (-?\d+\.\d+)", full_data)
            if score_regex:
                score = score_regex.groups()[0]
                data['scores'].append((filename, float(score)))

            pylint_data = short_data.splitlines()

            #Remove the module line that is at the top of each pylint
            if len(pylint_data) > 0:
                pylint_data.pop(0)
            data[filename] = pylint_data
            for line in pylint_data[:]:
                if line.startswith('E'):
                    data['errors'] += 1
                #Ignore pylint fatal errors (problem w/ pylint, not the code generally).
                if line.startswith('F'):
                    data[filename].remove(line)
            data['total'] += len(data[filename])

        if len(data['scores']) > 0:
            data['average'] = (sum([score[1] for score in data['scores']]) / len(data['scores']))
        else:
            data['average'] = 9  # Default average? Comes up when all files are new.
        print("Total: %s" % data['total'])
        print("Errors: %s" % data['errors'])
        print("Average score: %f" % data['average'])
        return data


def pylint_raw(options):
    """
    Use check_output to run pylint.
    Because pylint changes the exit code based on the code score,
    we have to wrap it in a try/except block.

    :param options:
    :return:
    """
    with open(os.devnull, 'w') as devnull:
        try:
            command = ['pylint']
            command.extend(options)
            data = subprocess.check_output(command, stderr=devnull)
        except subprocess.CalledProcessError as exception:
            data = exception.output
    return data
