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
import argparse
import os
from git import Repo
from contextlib import contextmanager
from pylint_validator import PylintValidator, above_score_threshold, no_new_errors

PYLINT_SCORE_THRESHOLD = 9


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


def dump_to_console(pylint_data):
    """
    Displays pylint data to the console.

    :param pylint_data:
    :return:
    """
    for key, value in pylint_data.items():
        if key not in ('errors', 'total', 'scores', 'average') and len(value) > 0:
            print "\n*********** {}".format(key)
            for line in value:
                print line.strip('\n')
            f_score = [score[1] for score in pylint_data['scores'] if score[0] == key][0]
            print "Score: {}".format(f_score)


def checkout(repository, target):
    """
    Check out target into the current directory.
    Target can be a branch, review Id, or commit.

    :param repository: Current git repository.
    :param target: Review ID, commit, branch.
    :return: Return the most recent commit ID (top of the git log).
    """
    # git fetch <remote> refs/changes/<review_id>
    #git checkout FETCH_HEAD
    repository.git.fetch([next(iter(repository.remotes)), target])
    repository.git.checkout("FETCH_HEAD")
    return repository.git.rev_parse(["--short", "HEAD"]).encode('ascii', 'ignore')


def get_files_changed(repository, review_id):
    """
    Get a list of files changed compared to the given review.
    Compares against current directory.

    :param repository: Git repository. Used to get remote.
      - By default uses first remote in list.
    :param review_id: Gerrit review ID.
    :return: List of file paths relative to current directory.
    """
    repository.git.fetch([next(iter(repository.remotes)), review_id])
    files_changed = repository.git.diff_tree(["--no-commit-id",
                                              "--name-only",
                                              "-r",
                                              "FETCH_HEAD"]).splitlines()
    print "Found {} files changed".format(len(files_changed))
    return files_changed


def pylint(file_list):
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
    print "Total: %s" % data['total']
    print "Errors: %s" % data['errors']
    print "Average score: %f" % data['average']
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
    #Format the message in a way that is readable both by shell command
    #as well as Gerrit (need to double quote, once for shell, once for gerrit).
    message = "'\"{}\"'".format(message)

    subprocess.check_output(["ssh",
                             "-p", str(os.environ.get("GERRIT_PORT", "29418")),
                             "{}@{}".format(user, gerrit),
                             "gerrit", "review", "--code-review " + score,
                             "-m", message, commit])


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
