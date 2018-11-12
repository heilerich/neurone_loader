# This file is part of neurone_loader
# (https://www.github.com/heilerich/neurone_loader)
# Copyright © 2018 Felix Heilmeyer.
#
# This code is released under the MIT License
# http://opensource.org/licenses/mit-license.php
# Please see the file LICENSE for details.

from setuptools import setup

setup(name='neurone_loader',
      version='0.1',
      description='Utilites for loading data recorded with NeurOne',
      url='http://github.com/heilerich/neurone_loader',
      author='Felix Heilmeyer',
      author_email='code@fehe.eu',
      license='MIT',
      packages=['neurone_loader'],
      zip_safe=False,
      install_requires=[
          'numpy',
          'pandas',
          'construct'
      ],
      zip_safe=False
      )