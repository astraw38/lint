from distutils.core import setup

setup(
    name='gerrit-pylinter',
    version='1.0',
    packages=['gerrit-pylinter'],
    url='https://github.com/astraw38/gerrit-pylinter',
    license='GNU GPL 2.0',
    author='Ashley Straw',
    author_email='strawac1@gmail.com',
    description='',
    install_requires=["git", "pylint"]
)
