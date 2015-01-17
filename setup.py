from distutils.core import setup

setup(
    name='gerritlinter',
    version='1.0',
    packages=['gerritlinter'],
    url='https://github.com/astraw38/gerritlinter',
    license='GNU GPL 2.0',
    author='Ashley Straw',
    author_email='strawac1@gmail.com',
    description='',
    install_requires=["git", "pylint"]
)
