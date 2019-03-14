NeuroneLoader
=============

.. image:: https://travis-ci.org/heilerich/neurone_loader.svg?branch=master
   :target: https://travis-ci.org/heilerich/neurone_loader
   :alt: Build Status

.. image:: https://coveralls.io/repos/github/heilerich/neurone_loader/badge.svg
   :target: https://coveralls.io/github/heilerich/neurone_loader
   :alt: Coverage Status
.. image:: https://readthedocs.org/projects/neurone-loader/badge/?version=latest
   :target: https://neurone-loader.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://img.shields.io/github/license/heilerich/neurone_loader.svg
   :target: https://github.com/heilerich/neurone_loader/blob/master/LICENSE
   :alt: License

.. image:: https://img.shields.io/pypi/v/neurone_loader.svg
   :target: https://pypi.org/project/neurone-loader/
   :alt: PyPi Package

.. image:: https://img.shields.io/pypi/pyversions/neurone_loader.svg
   :target: https://pypi.org/project/neurone-loader/
   :alt: Supported Python Versions

NeuroneLoader is a python module for loading neurophysiological data recorded with Bittium NeurOne (formerly MegaEMG).
It can also export it to container objects used by the popular `python-mne <https://mne-tools.github.io/stable/index.html>`_
framework.

Props to Andreas Henelius at Finnish Institute of Occupational Health for figuring out how
to read the NeurOne binary format in pure python as part of his
export2hdf_ project.

* `Installation`_
* `Quick start`_
* Documentation_

.. _Documentation: https://neurone-loader.readthedocs.io/en/latest/
.. _export2hdf: https://github.com/bwrc/export2hdf5

Installation
------------

.. code:: bash

   pip install neurone_loader

If you want to export to `python-mne <https://mne-tools.github.io/stable/index.html>`_ you must also install MNE and
all it's dependencies.

.. code:: bash

   pip install mne

.. _quick-start:

Quick start
-----------

.. code:: python

   >>> from neurone_loader import Recording
   >>> rec = Recording(path_to_recording_folder)
   >>> rec.event_codes
   array([  0,   1,  12,  13,  99, 128], dtype=int32)

Please note that because raw EEG recordings can be quite large this package is very memory aware. Most data will be
loaded from disk lazily, i.e. the moment you're actually accessing it, and redundant data will be removed from memory
as soon as it has been copied - unless you specify otherwise. Be advised that working with big recordings might still
require a lot of memory.

I recommend looking at the docstrings before executing anything and maybe having a look at Concepts section in
the Documentation_ before you start working with this package.

Contributing
------------

If you encounter any problem feel free to open a issue_ on GitHub. If you found a bug and want to
supply a fix or if you want to contribute a new feature open a `pull request`_. Just make sure that
your code is not breaking any tests and you also supply tests for your code. To run the tests you
must first get the test data:

.. code:: bash

   bash test/get_test_data.sh

Then you can run the tests with:

.. code:: bash

   python -m unittest discover -s test -t .


.. _issue: https://github.com/heilerich/neurone_loader/issues
.. _pull request: https://github.com/heilerich/neurone_loader/pulls