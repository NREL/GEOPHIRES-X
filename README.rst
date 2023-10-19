========
Overview
========

GEOPHIRES is a free and open-source geothermal techno-economic simulator. GEOPHIRES combines reservoir, wellbore, surface plant, and economic models to estimate the capital and operation and maintenance costs, instantaneous and lifetime energy production, and overall levelized cost of energy of a geothermal plant. Various reservoir conditions (EGS, doublets, etc.) and end-use options (electricity, direct-use heat, cogeneration) can be modeled. Users are encouraged to build upon to the GEOPHIRES framework to implement their own correlations and models.

GEOPHIRES-X is the successor version to `GEOPHIRES v2.0 <https://github.com/NREL/GEOPHIRES-v2>`_.
Ported from `malcolm-dsider/GEOPHIRES-X <https://github.com/malcolm-dsider/GEOPHIRES-X>`_
and `softwareengineerprogrammer/python-geophires-x <https://github.com/softwareengineerprogrammer/python-geophires-x>`_
using `ionelmc/cookiecutter-pylibrary <https://github.com/ionelmc/cookiecutter-pylibrary/>`_.

Free software: `MIT license <LICENSE>`_

.. start-badges

.. list-table::
    :stub-columns: 1

    * - tests
      - | |github-actions|
        |
    * - package
      - | |commits-since|

.. TODO add the following to package badge list once PyPy distribution enabled: |version| |wheel| |supported-versions| |supported-implementations|

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

.. |commits-since| image:: https://img.shields.io/github/commits-since/NREL/python-geophires-x/v3.2.0.svg
    :alt: Commits since latest release
    :target: https://github.com/NREL/python-geophires-x/compare/v3.2.0...main



.. end-badges

Installation
============

Install the in-development version with::

    pip install https://github.com/NREL/python-geophires-x/archive/main.zip

(Eventually package will be published to PyPi, enabling ``pip install geophires-x``)

Documentation
=============

* `How to extend GEOPHIRES-X <How-to-extend-GEOPHIRES-X.md>`_
* See `test_geophires_x.py <https://github.com/NREL/python-geophires-x/blob/main/tests/test_geophires_x.py>`_ for example usage of the client.
* `GEOPHIRES v2 user manual <References/GEOPHIRES%20v2.0%20User%20Manual.pdf>`_ (A GEOPHIRES-X-specific manual is pending as of 2023-10-10).


Development
===========

See `Development instructions in CONTRIBUTING.rst <CONTRIBUTING.rst#development>`_
