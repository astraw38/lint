from distutils.core import setup

setup(
    name='lint',
    version='1.2.1',
    packages=['lint', 'lint/utils', 'lint/validators', 'lint/linters'],
    url='https://github.com/astraw38/lint',
    download_url='https://github.com/astraw38/lint/tarball/1.2.1',
    license='GNU GPL 2.0',
    author='Ashley Straw',
    author_email='strawac1@gmail.com',
    description='',
    scripts=['bin/gpylinter.py'],
    install_requires=["gitpython", "pylint"]
)
