========
Overview
========

GEOPHIRES is a free and open-source geothermal techno-economic simulator. GEOPHIRES combines reservoir, wellbore, surface plant, and economic models to estimate the capital and operation and maintenance costs, instantaneous and lifetime energy production, and overall levelized cost of energy of a geothermal plant. Various reservoir conditions (EGS, doublets, etc.) and end-use options (electricity, direct-use heat, cogeneration) can be modeled. Users are encouraged to build upon to the GEOPHIRES framework to implement their own correlations and models.

Ported from https://github.com/malcolm-dsider/GEOPHIRES-X and https://github.com/softwareengineerprogrammer/python-geophires-x using https://github.com/ionelmc/cookiecutter-pylibrary/.

* Free software: MIT license

.. start-badges

.. list-table::
    :stub-columns: 1

    * - tests
      - | |github-actions|
        |
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |github-actions| image:: https://github.com/NREL/python-geophires-x/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/NREL/python-geophires-x/actions

.. |version| image:: https://img.shields.io/pypi/v/geophires-x.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/geophires-x

.. |wheel| image:: https://img.shields.io/pypi/wheel/geophires-x.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/geophires-x

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/geophires-x.svg
    :alt: Supported versions
    :target: https://pypi.org/project/geophires-x

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/geophires-x.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/geophires-x

.. |commits-since| image:: https://img.shields.io/github/commits-since/NREL/python-geophires-x/v/v/v1.3.0...main.svg.svg
    :alt: Commits since latest release
    :target: https://github.com/NREL/python-geophires-x/compare/v3.0.0...main



.. end-badges

Installation
============


Install the in-development version with::

    pip install https://github.com/NREL/python-geophires-x/archive/main.zip

(Eventually package will be published to PyPi, enabling ``pip install geophires-x``)


Dev Setup
=========

1. Setup and activate virtualenv (https://virtualenv.pypa.io/en/latest/installation.html#via-pip)::

    python -m venv venv
    source venv/bin/activate

2. Install dependencies in setup.py::

    pip install .

3. Setup pre-commit (https://pre-commit.com/)::

    pre-commit install


Documentation
=============


See https://github.com/NREL/python-geophires-x/blob/main/tests/test_geophires_x.py for example usage


Development
===========

To run all the tests run::

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
