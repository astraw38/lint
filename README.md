# Glint
Python script to automatically lint new reviews to gerrit. Designed to be run from within Jenkins via the Gerrit Trigger plugin


Glint is a python package to assist with automatic code reviews. It provides the following tools:

1. Get a list of files changed between the active gerrit branch and the specified gerrit review.
2. Lint the original files in the active gerrit branch.
3. Checkout the current review ID
4. Lint the changed files. 
5. Analyze the results according to specified validators.
6. Post the results of the validation to gerrit via SSH (+1/-1 score assigned, including a message). 

Glint uses the environmental variables set by Gerrit Trigger to do almost all of the configuration. You can still use it via command-line (with options!) for manual testing. 


You can also add a checkers to validators, which are simple functions to compare lint data that are passed to the validator. 

##Installation

pip install https://github.com/astraw38/glint


##Usage

For pylint, just use 'gpylinter.py'. It by default will use the 'Pylinter' plugin for .py files, as well as the default pylint validators. 

Glint provides the ability to plugin your own Linter or Validator classes. All you need to do is run 
```python
LintFactory.register_linter(NewLinter()) 
```
or 
```python
ValidatorFactory.register_validator(NewValidator())
```
    
When you run 'run_linters()' or 'run_validators()', it'll pick them up and use them. Your new Linters should derive from BaseLinter, and your new Validators should derive from BaseValidator. 

You can also customize the order of operations, or how comments/scores are posted to gerrit. Just look at gpylinter as an example. 
