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

.. TODO coverage badge https://github.com/NREL/python-geophires-x/issues/22

.. end-badges

Documentation
=============

User manuals:

- A GEOPHIRES-X-specific user manual `is pending <https://github.com/NREL/python-geophires-x/issues/23>`_ as of 2023-10-19. In the meantime, the `GEOPHIRES v2.0 user manual <References/GEOPHIRES%20v2.0%20User%20Manual.pdf>`_ remains partially relevant.

- `How to extend GEOPHIRES-X <How-to-extend-GEOPHIRES-X.md>`_

- `test_geophires_x.py <tests/test_geophires_x.py>`_ has examples of how to consume and call `GeophiresXClient <src/geophires_x_client/__init__.py#L14>`_ locally (i.e. if consuming GEOPHIRES-X as a pip package)


Installation
============

Strongly recommended prerequisite: always install in a `virtual environment <https://virtualenv.pypa.io/en/latest/installation.html#via-pip>`_ (rather than global site-packages).

To consume GEOPHIRES-X as a python package, install the in-development version with::

    pip install https://github.com/NREL/python-geophires-x/archive/main.zip

(Eventually package will be published to PyPi, enabling ``pip install geophires-x``)

If you wish to add your own extensions (as described in `How to extend GEOPHIRES-X <How-to-extend-GEOPHIRES-X.md>`_) one option is to do an `editable install <https://pip.pypa.io/en/stable/topics/local-project-installs/>`_::

   pip install -e git+https://github.com/NREL/python-geophires-x.git#egg=geophires-x

If you are interested in sharing your extensions with others (or even contributing them back to this repository),
follow `the Development instructions <CONTRIBUTING.rst#development>`_ instead.

Development
===========

See `Development instructions in CONTRIBUTING.rst <CONTRIBUTING.rst#development>`_
