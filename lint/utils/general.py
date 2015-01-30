"""
General utilities used by Gerrit-pylinter.

"""
from contextlib import contextmanager
import os
import subprocess
from collections import defaultdict


@contextmanager
def cd_ctx(directory):
    """
    Context manager. Stores current dir, then changes to given directory.
    At the end it changes back.
    :param directory:
    :return:
    """
    prevdir = os.path.abspath(os.curdir)
    if os.path.isdir(directory):
        os.chdir(directory)
    yield
    os.chdir(prevdir)


def dump_to_console(pylint_data):
    """
    Displays pylint data to the console.

    :param pylint_data:
    :return:
    """
    for key, value in list(pylint_data.items()):
        if key not in ('errors', 'total', 'scores', 'average') and len(value) > 0:
            print("\n*********** {}".format(key))
            for line in value:
                print(line.strip('\n'))
            f_score = [score[1] for score in pylint_data['scores'] if score[0] == key][0]
            print("Score: {}".format(f_score))


def post_to_gerrit(commit, score=0, message='', user='lunatest', gerrit=None):
    """
    Post the data to gerrit. This right now is a stub, as
    I'll need to write the code to post up to gerrit.

    :param commit: Commit ID of the review.
    :param message: Message to accompany the review score.
    :param user: SSH User for posting to gerrit.
    :param gerrit: Hostname of the gerrit server.
    :param score: Score to post to gerrit (+1/-1, etc)
    :return:
    """
    # ssh -p 29418 review.example.com gerrit review --code-review +1 <commit_id>
    if score > 0:
        score = "+{}".format(score)
    else:
        url = "{}job/{}/{}/consoleText".format(os.environ.get('JENKINS_URL'),
                                               os.environ.get('JOB_NAME'),
                                               os.environ.get('BUILD_NUMBER'))
        message = ("{}\r\n\r\n"
                   "Check output here: {}").format(message, url)
        score = str(score)
    # Format the message in a way that is readable both by shell command
    #as well as Gerrit (need to double quote, once for shell, once for gerrit).
    message = "'\"{}\"'".format(message)

    subprocess.check_output(["ssh",
                             "-p", str(os.environ.get("GERRIT_PORT", "29418")),
                             "{}@{}".format(user, gerrit),
                             "gerrit", "review", "--code-review " + score,
                             "-m", message, commit])


def sort_by_type(file_list):
    """
    Sorts a list of files into types.

    :param file_list: List of file paths.
    :return: {extension: [<list of file paths with that extension>]}
    """
    ret_dict = defaultdict(list)
    for filepath in file_list:
        _, ext = os.path.splitext(filepath)
        ret_dict[ext.replace('.', '')].append(filepath)

    return ret_dict
