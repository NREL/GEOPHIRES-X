========
Overview
========

Distributable python package version of GEOPHIRES-X.

Ported from https://github.com/malcolm-dsider/GEOPHIRES-X using https://github.com/ionelmc/cookiecutter-pylibrary/.

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

.. |github-actions| image:: https://github.com/softwareengineerprogrammer/python-geophires-x/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/softwareengineerprogrammer/python-geophires-x/actions

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

.. |commits-since| image:: https://img.shields.io/github/commits-since/softwareengineerprogrammer/python-geophires-x/v1.3.0.svg
    :alt: Commits since latest release
    :target: https://github.com/softwareengineerprogrammer/python-geophires-x/compare/v1.3.0...main



.. end-badges

Installation
============


Install the in-development version with::

    pip install https://github.com/softwareengineerprogrammer/python-geophires-x/archive/main.zip

(Eventually package will be published to PyPi, enabling ``pip install geophires-x``)



Documentation
=============


See https://github.com/softwareengineerprogrammer/python-geophires-x/blob/main/tests/test_geophires_x.py for example usage


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
