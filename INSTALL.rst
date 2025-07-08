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
