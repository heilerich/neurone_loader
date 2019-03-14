# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#  This file (setup.py) is part of neurone_loader                              -
#  (https://www.github.com/heilerich/neurone_loader)                           -
#  Copyright © 2019 Felix Heilmeyer.                                           -
#                                                                              -
#  This code is released under the MIT License                                 -
#  https://opensource.org/licenses/mit-license.php                             -
#  Please see the file LICENSE for details.                                    -
# ------------------------------------------------------------------------------

from setuptools import setup

import os
import codecs
import re

this_directory = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # noinspection PyArgumentEqualDefault
    with codecs.open(os.path.join(this_directory, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


def find_requirements(*file_paths):
    requirements_file = read(*file_paths)
    requirements = re.findall(r"^(.+)$", requirements_file, re.M)
    return requirements if requirements is not None else []


long_description = read('README.rst')
version_number = find_version('neurone_loader', '__init__.py')
requirements = find_requirements('requirements.txt')

setup(name='neurone_loader',
      version=version_number,
      description='Utilities for loading data recorded with NeurOne',
      long_description=long_description,
      long_description_content_type='text/x-rst',
      url='http://github.com/heilerich/neurone_loader',
      author='Felix Heilmeyer',
      author_email='code@fehe.eu',
      python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*, <4',
      license='MIT',
      packages=['neurone_loader'],
      keywords=['EEG', 'science', 'neuroscience', 'neurone', 'bittium', 'megaemg', 'MNE'],
      download_url='https://github.com/heilerich/neurone_loader/archive/v{}.tar.gz'.format(version_number),
      zip_safe=False,
      install_requires=requirements,
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Topic :: Scientific/Engineering'
      ]
      )
