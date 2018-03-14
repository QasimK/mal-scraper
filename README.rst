BRANCH:

Creating middleware.py

Issue: responses lib does not mock our request because we use a custom HTTPAdapter.
Solution: https://github.com/getsentry/responses/pull/189
Blocker: It is not approved and not merged.

========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - |travis| |requires| |codecov| |codacy|
    * - package
      - |version| |wheel| |supported-versions|

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

.. |wheel| image:: https://img.shields.io/pypi/wheel/mal-scraper.svg?style=flat
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/mal-scraper

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/mal-scraper.svg?style=flat
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/mal-scraper

.. end-badges


MyAnimeList Web Scraper (mal-scraper) is a Python library for gathering a
basic set of data about anime.

It can gather information about users from MAL including what anime they have
watched and their ratings. It can discover users on MAL, and retrieve some
very basic information about each anime. This information can be used to
analyse data.


Installation & Usage
====================

.. code-block:: bash

    pip install mal-scraper

Please use the `online documentation <https://mal-scraper.readthedocs.io/>`_ for
to get started.

The library follows `Semantic Versioning <http://semver.org/>`_.


Development
===========

Please see the `Contributing <https://mal-scraper.readthedocs.io/en/latest/contributing.html>`_
documentation page for full details, and especially look at the tips section.

After cloning, and creating a virtualenv, install the development dependencies::

    pip install -e .[develop]

To run the all tests, skipping the python interpreters you don't have::

    tox --skip-missing-interpreters

Project Notes:

- Tests will always mock requests to the internet. You can set the environment
  variable :code:`LIVE_RESPONSES=1` to properly test web scraping.
- You can look at coverage results inside :code:`htmlcov/index.html`.

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
