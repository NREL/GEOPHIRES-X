============
Installation
============

Strongly recommended prerequisite: always install in a `virtual environment <https://virtualenv.pypa.io/en/latest/installation.html#via-pip>`_ (rather than global site-packages).

To consume GEOPHIRES-X as a python package, install the in-development version with::

    pip install https://github.com/NREL/python-geophires-x/archive/main.zip

(Eventually package will be published to PyPi, enabling ``pip install geophires-x``)

If you wish to add your own extensions (as described in `How to extend GEOPHIRES-X <How-to-extend-GEOPHIRES-X.md>`__) one option is to do an `editable install <https://pip.pypa.io/en/stable/topics/local-project-installs/>`_::

   pip install -e git+https://github.com/NREL/python-geophires-x.git#egg=geophires-x

If you are interested in sharing your extensions with others (or even contributing them back to this repository),
follow `the Development instructions <CONTRIBUTING.rst#development>`_ instead.
