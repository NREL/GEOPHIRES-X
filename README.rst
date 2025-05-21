========
Overview
========

|GEOPHIRES Logo|

.. |GEOPHIRES Logo| image:: geophires-logo.png
    :alt: GEOPHIRES Logo

GEOPHIRES is a free and open-source geothermal techno-economic simulator.
GEOPHIRES combines reservoir, wellbore, surface plant, and economic models to estimate the capital and operation and maintenance costs,
instantaneous and lifetime energy production, and overall levelized cost of energy of a geothermal plant.
Various reservoir conditions (EGS, doublets, etc.) and end-use options (electricity, direct-use heat, cogeneration) can be modeled.
Users are encouraged to build upon to the GEOPHIRES framework to implement their own correlations and models.
See the `Documentation`_ section below for more information.

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

.. |commits-since| image:: https://img.shields.io/github/commits-since/softwareengineerprogrammer/GEOPHIRES-X/v3.9.9.svg
    :alt: Commits since latest release
    :target: https://github.com/softwareengineerprogrammer/GEOPHIRES-X/compare/v3.9.9...main

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

A web interface is available at `gtp.scientificwebservices.com/geophires <https://gtp.scientificwebservices.com/geophires>`__.

The short URL `bit.ly/geophires <https://bit.ly/geophires>`__ redirects to the same location.

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

GEOPHIRES combines reservoir, wellbore, surface plant, and economic and cost models
and correlations to estimate the capital and operation and maintenance costs,
instantaneous and lifetime energy production, and overall levelized cost of energy of a
geothermal plant.

The high-level software architecture is illustrated in the diagram below. Green, orange and blue rectangles
refer to internal GEOPHIRES components, external user-interface components, and
external reservoir simulators (TOUGH2), respectively. Rectangles with solid outline are
always executed during a simulation run; rectangles with dashed outline refer to optional
or user-provided components.

|GEOPHIRES Architecture Diagram|

.. |GEOPHIRES Architecture Diagram| image:: References/geophires-architecture-diagram_2024-11-20.png
    :alt: GEOPHIRES Architecture Diagram

GEOPHIRES has a variety of different reservoir models including (1) Multiple parallel fractures model;
(2) 1-Dimensional linear heat sweep model;
(3) M/A thermal drawdown parameter model;
(4) Percentage temperature drawdown model;
(5) User-provided reservoir temperature production data;
(6) Coupling to TOUGH2 external reservoir simulator;
(7) SUTRA: Reservoir Thermal Energy Storage (RTES; also known as Underground Thermal Energy Storage - UTES);
(8) Slender Body Theory (SBT);
(9) Cylindrical.

GEOPHIRES can simulate three different end-uses of the geothermal heat: (1)
direct-use heat (e.g. for industrial processing heating or residential space heating);
(2) electricity (with subcritical ORC, supercritical ORC, single-flash, or double-flash plant);
(3) co-generation of heat and electricity. The co-generation option considers bottoming
cycle, topping cycle, and parallel cycle.

GEOPHIRES has 5 economic models to calculate the levelized cost of heat or
electricity: (1) fixed charge rate (FCR) model;
(2) standard discounting levelized cost model;
(3) BICYCLE model;
(4) CLGS;
(5) SAM Single-owner PPA.

.. TODO link to SAM Economic Model docs

The capital and O&M costs for the different geothermal system components (exploration,
well drilling, surface plant, etc.) are either provided by the user or calculated with built-in
correlations.

For more information on the theoretical basis for GEOPHIRES see
`GEOPHIRES v2.0: updated geothermal techno‐economic simulation tool (Beckers & McCabe, 2019) <https://github.com/NREL/GEOPHIRES-X/blob/fb5caadfa419c3bd05de656a33700d085fbc0432/References/GEOPHIRES%20v2.0%20User%20Manual.pdf>`__
and `GEOPHIRES reference materials <References/references.md#geophires>`__.

Parameters
----------

Available parameters are documented in the `Parameters Reference <https://nrel.github.io/GEOPHIRES-X/parameters.html>`__.

Note that many parameters are interrelated and/or conditionally dependent on one another;
reviewing the GEOPHIRES example(s) relevant to your use case in the following section
is strongly recommended to gain a working understanding of how to construct valid sets of input parameters.


Examples
--------

GEOPHIRES includes a variety of example input files demonstrating its features for different types of geothermal systems
and case studies of real-world geothermal projects.
Starting with an existing GEOPHIRES example that is similar to your intended use/application can be an easier approach to using GEOPHIRES than constructing your own inputs from scratch.

Example input ``.txt`` files and corresponding case report ``.out`` files are available in the `tests/examples directory <tests/examples>`__ of the repository.
Example-specific web interface deeplinks are listed in the Link column.


.. list-table::
   :widths: 50 40 5 5
   :header-rows: 1

   * - Example
     - Input file
     - Case report file
     - Link
   * - Example 1: EGS Electricity
     - `example1.txt <tests/examples/example1.txt>`__
     - `.out <tests/examples/example1.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example1>`__
   * - Example 1 with Add-Ons
     - `example1_addons.txt <tests/examples/example1_addons.txt>`__
     - `.out <tests/examples/example1_addons.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example1_addons>`__
   * - Example 2: EGS Direct-Use Heat
     - `example2.txt <tests/examples/example2.txt>`__
     - `.out <tests/examples/example2.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example2>`__
   * - Example 3: EGS Co-generation
     - `example3.txt <tests/examples/example3.txt>`__
     - `.out <tests/examples/example3.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example3>`__
   * - Example 4: Hydrothermal Electricity
     - `example4.txt <tests/examples/example4.txt>`__
     - `.out <tests/examples/example4.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example4>`__
   * - Example 5: User-Provided Reservoir Data
     - `example5.txt <tests/examples/example5.txt>`__
     - `.out <tests/examples/example5.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example5>`__
   * - Example 6: TOUGH2 (Multiple Gradients)
     - `example6.txt <tests/examples/example6.txt>`__
     - `.out <tests/examples/example6.out>`__
     - \*
   * - Example 7: TOUGH2 (Single Gradient)
     - `example7.txt <tests/examples/example7.txt>`__
     - `.out <tests/examples/example7.out>`__
     - \*
   * - Example 8: Cornell Direct-Use Heat
     - `example8.txt <tests/examples/example8.txt>`__
     - `.out <tests/examples/example8.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example8>`__
   * - Example 9: Cornell Electricity
     - `example9.txt <tests/examples/example9.txt>`__
     - `.out <tests/examples/example9.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example9>`__
   * - Example 10: Heat Pump
     - `example10_HP.txt <tests/examples/example10_HP.txt>`__
     - `.out <tests/examples/example10_HP.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example10_HP>`__
   * - Example 11: Absorption Chiller
     - `example11_AC.txt <tests/examples/example11_AC.txt>`__
     - `.out <tests/examples/example11_AC.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example11_AC>`__
   * - Example 12: District Heating
     - `example12_DH.txt <tests/examples/example12_DH.txt>`__
     - `.out <tests/examples/example12_DH.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example12_DH>`__
   * - Example 13: Redrilling due to Drawdown
     - `example13.txt <tests/examples/example13.txt>`__
     - `.out <tests/examples/example13.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example13>`__
   * - CLGS: Coaxial sCO2: Heat
     - `Beckers_et_al_2023_Tabulated_Database_Coaxial_sCO2_heat.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Coaxial_sCO2_heat.txt>`__
     - `.out <tests/examples/Beckers_et_al_2023_Tabulated_Database_Coaxial_sCO2_heat.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=Beckers_et_al_2023_Tabulated_Database_Coaxial_sCO2_heat>`__
   * - CLGS: Coaxial Water: Heat
     - `Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat.txt>`__
     - `.out <tests/examples/Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=Beckers_et_al_2023_Tabulated_Database_Coaxial_water_heat>`__
   * - CLGS: Uloop sCO2: Electricity
     - `Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_elec.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_elec.txt>`__
     - `.out <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_elec.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_elec>`__
   * - CLGS: Uloop sCO2: Heat
     - `Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_heat.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_heat.txt>`__
     - `.out <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_heat.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=Beckers_et_al_2023_Tabulated_Database_Uloop_sCO2_heat>`__
   * - CLGS: Uloop Water: Electricity
     - `Beckers_et_al_2023_Tabulated_Database_Uloop_water_elec.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_water_elec.txt>`__
     - `.out <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_water_elec.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=Beckers_et_al_2023_Tabulated_Database_Uloop_water_elec>`__
   * - CLGS: Uloop Water: Heat
     - `Beckers_et_al_2023_Tabulated_Database_Uloop_water_heat.txt <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_water_heat.txt>`__
     - `.out <tests/examples/Beckers_et_al_2023_Tabulated_Database_Uloop_water_heat.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=Beckers_et_al_2023_Tabulated_Database_Uloop_water_heat>`__
   * - CLGS: SBT High Temperature
     - `example_SBT_Hi_T.txt <tests/examples/example_SBT_Hi_T.txt>`__
     - `.out <tests/examples/example_SBT_Hi_T.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example_SBT_Hi_T>`__
   * - CLGS: SBT Low Temperature
     - `example_SBT_Lo_T.txt <tests/examples/example_SBT_Lo_T.txt>`__
     - `.out <tests/examples/example_SBT_Lo_T.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example_SBT_Lo_T>`__
   * - SUTRA Example 1
     - `SUTRAExample1.txt <tests/examples/SUTRAExample1.txt>`__
     - `.out <tests/examples/SUTRAExample1.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=SUTRAExample1>`__
   * - Multiple Gradients
     - `example_multiple_gradients.txt <tests/examples/example_multiple_gradients.txt>`__
     - `.out <tests/examples/example_multiple_gradients.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example_multiple_gradients>`__
   * - Investment Tax Credit
     - `example_ITC.txt <tests/examples/example_ITC.txt>`__
     - `.out <tests/examples/example_ITC.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example_ITC>`__
   * - Production Tax Credit
     - `example_PTC.txt <tests/examples/example_PTC.txt>`__
     - `.out <tests/examples/example_PTC.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example_PTC>`__
   * - Fervo Project Red (2023)
     - `Fervo_Norbeck_Latimer_2023.txt <tests/examples/Fervo_Norbeck_Latimer_2023.txt>`__
     - `.out <tests/examples/Fervo_Norbeck_Latimer_2023.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=Fervo_Norbeck_Latimer_2023>`__
   * - Fervo Cape Station 1: 2023 Results
     - `Fervo_Project_Cape.txt <tests/examples/Fervo_Project_Cape.txt>`__
     - `.out <tests/examples/Fervo_Project_Cape.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=Fervo_Project_Cape>`__
   * - Fervo Cape Station 2: 2024 Results
     - `Fervo_Project_Cape-2.txt <tests/examples/Fervo_Project_Cape-2.txt>`__
     - `.out <tests/examples/Fervo_Project_Cape-2.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=Fervo_Project_Cape-2>`__
   * - Fervo Cape Station 3: 400 MWe Production
     - `Fervo_Project_Cape-3.txt <tests/examples/Fervo_Project_Cape-3.txt>`__
     - `.out <tests/examples/Fervo_Project_Cape-3.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=Fervo_Project_Cape-3>`__
   * - Superhot Rock (SHR) Example 1
     - `example_SHR-1.txt <tests/examples/example_SHR-1.txt>`__
     - `.out <tests/examples/example_SHR-1.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example_SHR-1>`__
   * - Superhot Rock (SHR) Example 2
     - `example_SHR-2.txt <tests/examples/example_SHR-2.txt>`__
     - `.out <tests/examples/example_SHR-2.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example_SHR-2>`__
   * - SAM Single Owner PPA
     - `example_SAM-single-owner-PPA.txt <tests/examples/example_SAM-single-owner-PPA.txt>`__
     - `.out <tests/examples/example_SAM-single-owner-PPA.out>`__
     - `link <https://gtp.scientificwebservices.com/geophires?geophires-example-id=example_SAM-single-owner-PPA>`__

.. raw:: html

   <embed>
      <i>* TOUGH2 is not currently supported in the web interface. Comment on <a href="https://github.com/softwareengineerprogrammer/geothermal-ui/issues/15">this tracking issue</a> to request web interface support for TOUGH2.</i>
   </embed>

Videos
------

`NREL GEOPHIRES Workshop: Features Overview & Examples <https://www.youtube.com/watch?v=KsFvpvXjOB4>`__

`NREL GEOPHIRES Workshop: Case Studies <https://youtu.be/uMUDTUL6yWg>`__

HIP-RA: Heat in Place - Resource Assessment
-------------------------------------------

`HIP-RA-X README <src/hip_ra_x/README.md>`__

`HIP-RA-X Parameters Reference <https://nrel.github.io/GEOPHIRES-X/hip_ra_x_parameters.html>`__

A HIP-RA web interface is available at `gtp.scientificwebservices.com/hip-ra <https://gtp.scientificwebservices.com/hip-ra>`__.


Monte Carlo
-----------

`Monte Carlo User Guide <https://nrel.github.io/GEOPHIRES-X/Monte-Carlo-User-Guide.html>`__

A Monte Carlo web interface is available at `gtp.scientificwebservices.com/monte-carlo <https://gtp.scientificwebservices.com/monte-carlo>`__.

Extending GEOPHIRES-X
---------------------
`How to extend GEOPHIRES-X <docs/How-to-extend-GEOPHIRES-X.md#how-to-extend-geophires-x>`__ user guide

`Extension example: SUTRA <https://github.com/NREL/GEOPHIRES-X/commit/984cb4da1505667adb2c45cb1297cab6550774bd#diff-5b1ea85ce061b9a1137a46c48d2d293126224d677d3ab38d9b2f4dcfc4e1674e>`__


Additional Documentation
------------------------

Additional materials can be found in `/References </References/references.md>`__.


Development
===========

If you are interested in sharing your extensions with others, or even contributing them back to this repository,
you may want to follow `the Development instructions <CONTRIBUTING.rst#development>`__.
(You can also create a fork after doing an editable install so don't worry about picking this method if you're unsure.)

.. TODO feedback section - why user feedback is important/valuable, how to file issues/contact authors

.. TODO FAQ/trivia section - "HDR" naming (HDR.out, HDR.json) is for Hot Dry Rock
