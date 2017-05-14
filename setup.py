"""
Created on Mar 26, 2015

@author: woodd
"""
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, 'README.md')
if os.path.isfile(readme_path):
    with open(readme_path) as f:
        README = f.read()
else:
    README = None

install_requires = [
    'pywin32',
    'keyring',
    'lxml',
    'beautifulsoup4',
    ]

extras_require = {
    }

tests_require = [
    'nose',
    'coverage',
]

setup(name='microstrategy_api',
      version='0.1',
      description='MicroStrategy API Interface',
      long_description=README,
      classifiers=[],
      author='Derek Wood',
      author_email='9jym-buur@spamex.com',
      url='',
      keywords='',
      packages=find_packages(),
      install_requires=install_requires,
      extras_require=extras_require,
      tests_require=tests_require,
      )
