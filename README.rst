========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |requires|
        | |codecov|
        | |codacy|
    * - package
      - |version| |downloads| |wheel| |supported-versions| |supported-implementations|

.. |docs| image:: https://readthedocs.org/projects/mal-scraper/badge/?style=flat
    :target: https://readthedocs.org/projects/mal-scraper
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/QasimK/mal-scraper.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/QasimK/mal-scraper

.. |requires| image:: https://requires.io/github/QasimK/mal-scraper/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/QasimK/mal-scraper/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/QasimK/mal-scraper/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/QasimK/mal-scraper

.. |codacy| image:: https://img.shields.io/codacy/77e1509bdc184167864233483afefd00.svg?style=flat
    :target: https://www.codacy.com/app/QasimK/mal-scraper
    :alt: Codacy Code Quality Status

.. |version| image:: https://img.shields.io/pypi/v/mal-scraper.svg?style=flat
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/mal-scraper

.. |downloads| image:: https://img.shields.io/pypi/dm/mal-scraper.svg?style=flat
    :alt: PyPI Package monthly downloads
    :target: https://pypi.python.org/pypi/mal-scraper

.. |wheel| image:: https://img.shields.io/pypi/wheel/mal-scraper.svg?style=flat
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/mal-scraper

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/mal-scraper.svg?style=flat
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/mal-scraper

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/mal-scraper.svg?style=flat
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/mal-scraper


.. end-badges

 MyAnimeList web scraper is a Python library for gathering data for analysis.


Usage
=====

Use the [online documentation](https://mal-scraper.readthedocs.io/), and just::

    pip install mal-scraper


Development
===========

After cloning, and creating a virtualenv, install the development dependencies::

    pip install -e .[develop]

You should install Python interpreters 3.3, 3.4, 3.5, and pypy because tox will
test on all of them.
(Hints: `Linux <https://askubuntu.com/questions/125342/how-can-i-install-python-2-6-on-12-04>`_.)

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
