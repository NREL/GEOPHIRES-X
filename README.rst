========
Overview
========

|GEOPHIRES Logo|

.. |GEOPHIRES Logo| image:: geophires-logo.png
    :alt: GEOPHIRES Logo

GEOPHIRES is a free and open-source geothermal techno-economic simulator. GEOPHIRES combines reservoir, wellbore, surface plant, and economic models to estimate the capital and operation and maintenance costs, instantaneous and lifetime energy production, and overall levelized cost of energy of a geothermal plant. Various reservoir conditions (EGS, doublets, etc.) and end-use options (electricity, direct-use heat, cogeneration) can be modeled. Users are encouraged to build upon to the GEOPHIRES framework to implement their own correlations and models.

GEOPHIRES-X is the successor version to `GEOPHIRES v2.0 <https://github.com/NREL/GEOPHIRES-v2>`__ (see `CHANGELOG <CHANGELOG.rst>`__ for more info).

Free software: `MIT license <LICENSE>`__

.. start-badges

.. list-table::
    :stub-columns: 1

    * - tests
      - | |github-actions|
    * - package
      - | |commits-since|
.. TODO add the following to package badge list once PyPy distribution enabled: |version| |wheel| |supported-versions| |supported-implementations|
..    * - docs
..      - | |docs|


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

.. |commits-since| image:: https://img.shields.io/github/commits-since/NREL/python-geophires-x/v3.3.0.svg
    :alt: Commits since latest release
    :target: https://github.com/NREL/python-geophires-x/compare/v3.3.0...main

.. |docs| image:: https://readthedocs.org/projects/python-geophires-x/badge/?style=flat
    :target: https://nrel.github.io/python-geophires-x
    :alt: Documentation Status

.. TODO coverage badge https://github.com/NREL/python-geophires-x/issues/22

.. end-badges

Getting Started
===============

Web Interface
-------------

A web interface is available at `tinyurl.com/geophires <https://tinyurl.com/geophires>`__

Installation
------------

Strongly recommended prerequisite: always install in a `virtual environment <https://virtualenv.pypa.io/en/latest/installation.html#via-pip>`__ (rather than global site-packages).

To consume GEOPHIRES-X as a python package, install the in-development version with::

    pip install https://github.com/NREL/python-geophires-x/archive/main.zip

.. (Eventually package will be published to PyPi, enabling ``pip install geophires-x``)

If you wish to add your own extensions (as described in `How to extend GEOPHIRES-X <docs/How-to-extend-GEOPHIRES-X.md#how-to-extend-geophires-x>`__) one option is to do an `editable install <https://pip.pypa.io/en/stable/topics/local-project-installs/>`__::

   pip install -e git+https://github.com/NREL/python-geophires-x.git#egg=geophires-x

If you are interested in sharing your extensions with others (or even contributing them back to this repository),
follow `the Development instructions <CONTRIBUTING.rst#development>`__ instead.

Usage
-----

Python
^^^^^^

Example usage in Python:

.. code:: python

    from geophires_x_client import GeophiresXClient
    from geophires_x_client.geophires_input_parameters import GeophiresInputParameters

    client = GeophiresXClient()
    result = client.get_geophires_result(
                GeophiresInputParameters(
                    {
                        'End-Use Option': 2,
                        'Reservoir Model': 1,
                        'Time steps per year': 1,
                        'Reservoir Depth': 3,
                        'Gradient 1': 50,
                        'Maximum Temperature': 250,
                    }
                )
            )

    with open(result.output_file_path,'r') as f:
        print(f.read())

You may also pass parameters as a text file:

.. code:: python

    from pathlib import Path
    from geophires_x_client import GeophiresXClient
    from geophires_x_client.geophires_input_parameters import GeophiresInputParameters

    # https://github.com/NREL/python-geophires-x/blob/main/tests/examples/example1.txt
    example_file_path = Path('tests/examples/example1.txt').absolute()

    client = GeophiresXClient()
    result = client.get_geophires_result(
                GeophiresInputParameters(from_file_path=example_file_path)
            )

    with open(result.output_file_path,'r') as f:
        print(f.read())


`test_geophires_x.py <tests/test_geophires_x.py>`__ has additional examples of how to consume and call `GeophiresXClient <src/geophires_x_client/__init__.py#L14>`__.

Command Line
^^^^^^^^^^^^

If you installed with pip, you may run GEOPHIRES from the command line, passing your input file as an argument::

   python -mgeophires_x my_geophires_input.txt

Parameters
^^^^^^^^^^

Available parameters are documented in the `Parameters Reference <https://nrel.github.io/python-geophires-x/parameters.html>`__.

Examples
^^^^^^^^

A variety of example input ``.txt`` files are available in the `tests/examples directory of the repository <tests/examples>`__:

- `example1.txt <tests/examples/example1.txt>`__
- `example1_addons.txt <tests/examples/example1_addons.txt>`__
- `example2.txt <tests/examples/example2.txt>`__
- `example3.txt <tests/examples/example3.txt>`__
- `example4.txt <tests/examples/example4.txt>`__
- `example5.txt <tests/examples/example5.txt>`__
- `example8.txt <tests/examples/example8.txt>`__
- `example9.txt <tests/examples/example9.txt>`__
- `example10_HP.txt <tests/examples/example10_HP.txt>`__
- `example11_AC.txt <tests/examples/example11_AC.txt>`__
- `example12_DH.txt <tests/examples/example12_DH.txt>`__
- `example13.txt <tests/examples/example13.txt>`__
- `Beckers_et_al_2023_Tabulated_Database_Coaxial_sCO2_heat.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Coaxial_sCO2_heat.txt>`__
- `Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat.txt>`__
- `Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_elec.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_elec.txt>`__
- `Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_heat.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_heat.txt>`__
- `Beckers_et_al_2023_Tabulated_Database_Uloop_water_elec.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_water_elec.txt>`__
- `Beckers_et_al_2023_Tabulated_Database_Uloop_water_heat.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_water_heat.txt>`__
- `SUTRAExample1.txt <tests/examples/SUTRAExample1.txt>`__
- `example_multiple_gradients.txt <tests/examples/example_multiple_gradients.txt>`__


Documentation
=============

* `Parameters Reference <https://nrel.github.io/python-geophires-x/parameters.html>`__
* `How to extend GEOPHIRES-X <docs/How-to-extend-GEOPHIRES-X.md#how-to-extend-geophires-x>`__ user guide

  - `Extension example: SUTRA <https://github.com/NREL/python-geophires-x/commit/984cb4da1505667adb2c45cb1297cab6550774bd#diff-5b1ea85ce061b9a1137a46c48d2d293126224d677d3ab38d9b2f4dcfc4e1674e>`__

The `GEOPHIRES v2.0 (previous version's) user manual <References/GEOPHIRES%20v2.0%20User%20Manual.pdf>`__ describes GEOPHIRES's high-level software architecture.

Other Documentation:

- Theoretical basis for GEOPHIRES:  `GEOPHIRES v2.0: updated geothermal techno‐economic simulation tool <References/Beckers%202019%20GEOPHIRES%20v2.pdf>`__
- Additional materials in `/References </References>`__


Development
===========

See `Development instructions in CONTRIBUTING <CONTRIBUTING.rst#development>`__
