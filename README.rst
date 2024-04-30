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

.. |commits-since| image:: https://img.shields.io/github/commits-since/softwareengineerprogrammer/GEOPHIRES-X/v3.4.26.svg
    :alt: Commits since latest release
    :target: https://github.com/softwareengineerprogrammer/GEOPHIRES-X/compare/v3.4.26...main

.. |docs| image:: https://readthedocs.org/projects/GEOPHIRES-X/badge/?style=flat
    :target: https://nrel.github.io/GEOPHIRES-X
    :alt: Documentation Status

.. TODO coverage badge https://github.com/NREL/GEOPHIRES-Xx/issues/22

.. end-badges

Getting Started
===============

Web Interface
-------------

A web interface is available at `tinyurl.com/geophires <https://tinyurl.com/geophires>`__

Installation
------------

Editable Installation (Recommended)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An editable installation is recommended for most users. It will allow you to run GEOPHIRES-X locally,
view its python files in an IDE or text editor,
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

Pip Package
^^^^^^^^^^^

If you do not need to view or edit GEOPHIRES-X source code, you can consume GEOPHIRES-X as a regular, non-editable python package::

    pip3 install https://github.com/NREL/GEOPHIRES-X/archive/main.zip


.. (Eventually package will be published to PyPi, enabling ``pip install geophires-x``)


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
                    "Reservoir Model": 1,
                    "Reservoir Depth": 3,
                    "Number of Segments": 1,
                    "Gradient 1": 50,
                    "Number of Production Wells": 2,
                    "Number of Injection Wells": 2,
                    "Production Well Diameter": 7,
                    "Injection Well Diameter": 7,
                    "Ramey Production Wellbore Model": 1,
                    "Production Wellbore Temperature Drop": .5,
                    "Injection Wellbore Temperature Gain": 0,
                    "Production Flow Rate per Well": 55,
                    "Fracture Shape": 3,
                    "Fracture Height": 900,
                    "Reservoir Volume Option": 3,
                    "Number of Fractures": 20,
                    "Reservoir Volume": 1000000000,
                    "Water Loss Fraction": .02,
                    "Productivity Index": 5,
                    "Injectivity Index": 5,
                    "Injection Temperature": 50,
                    "Maximum Drawdown": 1,
                    "Reservoir Heat Capacity": 1000,
                    "Reservoir Density": 2700,
                    "Reservoir Thermal Conductivity": 2.7,
                    "End-Use Option": 1,
                    "Power Plant Type": 2,
                    "Circulation Pump Efficiency": .8,
                    "Utilization Factor": .9,
                    "Surface Temperature": 20,
                    "Ambient Temperature": 20,
                    "Plant Lifetime": 30,
                    "Economic Model": 1,
                    "Fixed Charge Rate": .05,
                    "Inflation Rate During Construction": 0,
                    "Well Drilling and Completion Capital Cost Adjustment Factor": 1,
                    "Well Drilling Cost Correlation": 1,
                    "Reservoir Stimulation Capital Cost Adjustment Factor": 1,
                    "Surface Plant Capital Cost Adjustment Factor": 1,
                    "Field Gathering System Capital Cost Adjustment Factor": 1,
                    "Exploration Capital Cost Adjustment Factor": 1,
                    "Wellfield O&M Cost Adjustment Factor": 1,
                    "Surface Plant O&M Cost Adjustment Factor": 1,
                    "Water Cost Adjustment Factor": 1,
                    "Print Output to Console": 1,
                    "Time steps per year": 6
                })
            )

    with open(result.output_file_path, 'r') as f:
        print(f.read())

If you followed the editable installation example above, put this code in ``my-geophires-project/main.py``, then run::

   python main.py

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

Other Documentation:
--------------------
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
