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
        | |coverage|
    * - package
      - | |commits-since|
        | |code-style|
        | |license|

.. TODO add the following to package badge list once PyPy distribution enabled: |version| |wheel| |supported-versions| |supported-implementations|
..    * - docs
..      - | |docs|


.. |github-actions| image:: https://github.com/NREL/GEOPHIRES-X/actions/workflows/github-actions.yml/badge.svg
    :alt: GitHub Actions Build Status
    :target: https://github.com/NREL/GEOPHIRES-X/actions

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

.. |commits-since| image:: https://img.shields.io/github/commits-since/softwareengineerprogrammer/GEOPHIRES-X/v3.4.42.svg
    :alt: Commits since latest release
    :target: https://github.com/softwareengineerprogrammer/GEOPHIRES-X/compare/v3.4.42...main

.. |docs| image:: https://readthedocs.org/projects/GEOPHIRES-X/badge/?style=flat
    :target: https://nrel.github.io/GEOPHIRES-X
    :alt: Documentation Status

.. |coverage| image:: https://coveralls.io/repos/github/NREL/GEOPHIRES-X/badge.svg?branch=main
    :target: https://coveralls.io/github/NREL/GEOPHIRES-X?branch=main
    :alt: Coverage Status

.. |code-style| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/NREL/GEOPHIRES-X/blob/main/.pre-commit-config.yaml
    :alt: Code Style: black

.. |license| image:: https://img.shields.io/badge/license-MIT-green.svg
    :target: https://github.com/NREL/GEOPHIRES-X/blob/main/LICENSE
    :alt: MIT license

.. end-badges

Getting Started
===============

Web Interface
-------------

A web interface is available at `scientificwebservices.com/tools/geophires <https://scientificwebservices.com/tools/geophires>`__.

The short URL `bit.ly/GEOPHIRES <https://bit.ly/GEOPHIRES>`__ redirects to the same location.

Installation
------------

Pip Package
^^^^^^^^^^^

If you do not need to view or edit GEOPHIRES-X source code, you can consume GEOPHIRES-X as a regular, non-editable python package::

    pip3 install https://github.com/NREL/GEOPHIRES-X/archive/main.zip


.. (Eventually package will be published to PyPi, enabling ``pip install geophires-x``)


Editable Installation (Recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An editable installation is recommended for most users. It will allow you to run GEOPHIRES-X locally,
view its Python files in an IDE or text editor,
and create your own extensions as described in `How to extend GEOPHIRES-X <docs/How-to-extend-GEOPHIRES-X.md#how-to-extend-geophires-x>`__.

Prerequisites:

1. Python 3.8+: You must have Python 3.8 or later installed on your machine. Python can be downloaded at `python.org/downloads <https://www.python.org/downloads/>`__. (On Ubuntu: ``alias python=python3`` if not aliased already.)
2. `Git <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`__
3. Virtual environment (aka ``virtualenv``): `Install virtual environment on your machine <https://virtualenv.pypa.io/en/latest/installation.html#via-pip>`__ if you don't have it already
4. On Windows, you will need Admin privileges (required to successfully activate the virtual environment)

Steps:

1. Open a command line (i.e. Terminal on Mac, PowerShell on Windows)
2. Create a directory for GEOPHIRES::

    mkdir my-geophires-project
    cd my-geophires-project

3. Create a virtual environment::

    python -m venv venv

4. Source the virtual environment:

   - Windows::

       venv\Scripts\activate

   - macOS/Linux::

       source venv/bin/activate

5. Install the ``geophires-x`` package::

    pip3 install -e git+https://github.com/NREL/GEOPHIRES-X.git#egg=geophires-x --src .

6. Run on an example file::

    cd geophires-x
    cd tests
    cd examples
    python -mgeophires_x example1.txt

7. View and edit source code by opening the ``my-geophires-project/`` directory in an IDE or editor such as `PyCharm <https://www.jetbrains.com/pycharm/>`__, `Spyder <https://www.spyder-ide.org/>`__, or `Visual Studio Code <https://code.visualstudio.com/>`__. The GEOPHIRES-X source code will be located in the ``my-geophires-project/geophires-x`` directory. You can add your own python files in ``my-geophires-x/`` that use the source as a module as shown below.

To update the editable installation with the latest GEOPHIRES version::

    cd geophires-x
    git pull
    # resolve merge conflicts, if any
    pip install -e .



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
                GeophiresInputParameters({
                    "Gradient 1": "69",
                    "Reservoir Depth": "5",
                    "End-Use Option": "1",
                    "Power Plant Type": "4"
                })
            )

    with open(result.output_file_path, 'r') as f:
        print(f.read())

If you followed the editable installation example above, put this code in ``my-geophires-project/main.py``, then run::

   python main.py

You will then see output including a case report::

    (venv) ➜  my-geophires-project python main.py
    No valid plant outlet pressure provided. GEOPHIRES will assume default plant outlet pressure (100 kPa)
    No valid plant outlet pressure provided. GEOPHIRES will assume default plant outlet pressure (100 kPa)

                                   *****************
                                   ***CASE REPORT***
                                   *****************

    Simulation Metadata
    ----------------------
     GEOPHIRES Version: 3.4.42
     Simulation Date: 2024-07-08
     Simulation Time:  10:07
     Calculation Time:      0.047 sec

                               ***SUMMARY OF RESULTS***

          End-Use Option: Electricity
          Average Net Electricity Production:                    23.94 MW
          Electricity breakeven price:                            5.04 cents/kWh

    [...]


You may also pass parameters as a text file:

.. code:: python

    from pathlib import Path
    from geophires_x_client import GeophiresXClient
    from geophires_x_client.geophires_input_parameters import GeophiresInputParameters

    # https://github.com/NREL/GEOPHIRES-X/blob/main/tests/examples/example1.txt
    example_file_path = Path('geophires-x/tests/examples/example1.txt').absolute()

    client = GeophiresXClient()
    result = client.get_geophires_result(
                GeophiresInputParameters(from_file_path=example_file_path)
            )

    with open(result.output_file_path, 'r') as f:
        print(f.read())


`test_geophires_x.py <tests/test_geophires_x.py>`__ has additional examples of how to consume and call `GeophiresXClient <src/geophires_x_client/__init__.py#L14>`__.


Command Line
^^^^^^^^^^^^

If you installed with pip (editable or non-), you may run GEOPHIRES from the command line, passing your input file as an argument::

   python -mgeophires_x my_geophires_input.txt

You may also optionally pass the output file as well::

   python -mgeophires_x my_geophires_input.txt my_geophires_result.out

(If you do not pass an output file argument a default name will be used.)


Documentation
=============

Examples
--------

A variety of example input ``.txt`` and corresponding ``.out`` files are available in the `tests/examples directory of the repository <tests/examples>`__:

- `example1.txt <tests/examples/example1.txt>`__ / `example1.out <tests/examples/example1.out>`__
- `example1_addons.txt <tests/examples/example1_addons.txt>`__ / `example1_addons.out <tests/examples/example1_addons.out>`__
- `example2.txt <tests/examples/example2.txt>`__ / `example2.out <tests/examples/example2.out>`__
- `example3.txt <tests/examples/example3.txt>`__ / `example3.out <tests/examples/example3.out>`__
- `example4.txt <tests/examples/example4.txt>`__ / `example4.out <tests/examples/example4.out>`__
- `example5.txt <tests/examples/example5.txt>`__ / `example5.out <tests/examples/example5.out>`__
- `example8.txt <tests/examples/example8.txt>`__ / `example8.out <tests/examples/example8.out>`__
- `example9.txt <tests/examples/example9.txt>`__ / `example9.out <tests/examples/example9.out>`__
- `example10_HP.txt <tests/examples/example10_HP.txt>`__ / `example10_HP.out <tests/examples/example10_HP.out>`__
- `example11_AC.txt <tests/examples/example11_AC.txt>`__ / `example11_AC.out <tests/examples/example11_AC.out>`__
- `example12_DH.txt <tests/examples/example12_DH.txt>`__ / `example12_DH.out <tests/examples/example12_DH.out>`__
- `example13.txt <tests/examples/example13.txt>`__ / `example13.out <tests/examples/example13.out>`__
- `Beckers_et_al_2023_Tabulated_Database_Coaxial_sCO2_heat.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Coaxial_sCO2_heat.txt>`__ / `Beckers_et_al_2023_Tabulated_Database_Coaxial_sCO2_heat.out <tests/examples/Beckers_et_al_2023_Tabulated_Database_Coaxial_sCO2_heat.out>`__
- `Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat.txt>`__ / `Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat.out <tests/examples/Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat.out>`__
- `Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_elec.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_elec.txt>`__ / `Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_elec.out <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_elec.out>`__
- `Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_heat.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_heat.txt>`__ / `Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_heat.out <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_heat.out>`__
- `Beckers_et_al_2023_Tabulated_Database_Uloop_water_elec.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_water_elec.txt>`__ / `Beckers_et_al_2023_Tabulated_Database_Uloop_water_elec.out <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_water_elec.out>`__
- `Beckers_et_al_2023_Tabulated_Database_Uloop_water_heat.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_water_heat.txt>`__ / `Beckers_et_al_2023_Tabulated_Database_Uloop_water_heat.out <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_water_heat.out>`__
- `SUTRAExample1.txt <tests/examples/SUTRAExample1.txt>`__ / `SUTRAExample1.out <tests/examples/SUTRAExample1.out>`__
- `example_multiple_gradients.txt <tests/examples/example_multiple_gradients.txt>`__ / `example_multiple_gradients.out <tests/examples/example_multiple_gradients.out>`__
- `Fervo_Norbeck_Latimer_2023.txt <tests/examples/Fervo_Norbeck_Latimer_2023.txt>`__ / `Fervo_Norbeck_Latimer_2023.out <tests/examples/Fervo_Norbeck_Latimer_2023.out>`__
- `example_SHR-1.txt <tests/examples/example_SHR-1.txt>`__ / `example_SHR-1.out <tests/examples/example_SHR-1.out>`__
- `example_SHR-2.txt <tests/examples/example_SHR-2.txt>`__ / `example_SHR-2.out <tests/examples/example_SHR-2.out>`__

An interactive table of examples is available at `gtp.scientificwebservices.com/geophires <https://gtp.scientificwebservices.com/geophires>`__, under the Examples tab.

Parameters
----------

Available parameters are documented in the `Parameters Reference <https://nrel.github.io/GEOPHIRES-X/parameters.html>`__.


Extending GEOPHIRES-X
---------------------
* `How to extend GEOPHIRES-X <docs/How-to-extend-GEOPHIRES-X.md#how-to-extend-geophires-x>`__ user guide

  - `Extension example: SUTRA <https://github.com/NREL/GEOPHIRES-X/commit/984cb4da1505667adb2c45cb1297cab6550774bd#diff-5b1ea85ce061b9a1137a46c48d2d293126224d677d3ab38d9b2f4dcfc4e1674e>`__

Monte Carlo
-----------

`Monte Carlo User Guide <https://softwareengineerprogrammer.github.io/GEOPHIRES-X/Monte-Carlo-User-Guide.html>`__

Additional Documentation
------------------------
The `GEOPHIRES v2.0 (previous version's) user manual <References/GEOPHIRES%20v2.0%20User%20Manual.pdf>`__ describes GEOPHIRES's high-level software architecture.

Theoretical basis for GEOPHIRES:  `GEOPHIRES v2.0: updated geothermal techno‐economic simulation tool <References/Beckers%202019%20GEOPHIRES%20v2.pdf>`__

Additional materials in `/References </References>`__


Development
===========

If you are interested in sharing your extensions with others, or even contributing them back to this repository,
you may want to follow `the Development instructions <CONTRIBUTING.rst#development>`__.
(You can also create a fork after doing an editable install so don't worry about picking this method if you're unsure.)

.. TODO feedback section - why user feedback is important/valuable, how to file issues/contact authors

.. TODO FAQ/trivia section - "HDR" naming (HDR.out, HDR.json) is for Hot Dry Rock
