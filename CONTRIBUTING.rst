============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Development
===========

To set up ``python-geophires-x`` for local development:

1. Fork `python-geophires-x <https://github.com/NREL/python-geophires-x>`_
   (look for the "Fork" button).

2. Enable Actions on your fork.

3. Clone your fork locally::

    git clone git@github.com:<your GitHub username>/python-geophires-x.git



Local Setup
-----------

Prerequisite: Follow fork & clone instructions above. Then:

1. Set up and activate `virtualenv <https://virtualenv.pypa.io/en/latest/installation.html#via-pip>`_::

    python -m venv venv
    source venv/bin/activate

2. Install dependencies in setup.py::

    pip install -e .

3. Set up `pre-commit <https://pre-commit.com/>`_::

    pre-commit install

4. When you're done making changes run all the checks and docs builder with one command::

    tox

5. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Your detailed description of your changes."
    git push origin

6. Submit a pull request through the GitHub website.

Tox tests
---------

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

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just make the pull request.

For merging, you should:

1. Include passing tests (run ``tox``).
2. Update documentation when there's new API, functionality etc.
3. Add a note to ``CHANGELOG.rst`` about the changes.
4. Add yourself to ``AUTHORS.rst``.

Tips
----

To run a subset of tests::

    tox -e envname -- pytest -k test_myfeature

To run all the test environments in *parallel*::

    tox -p auto

Bug reports
===========

When `reporting a bug <https://github.com/NREL/python-geophires-x/issues>`_ please include:

    * Your operating system name and version.
    * Any details about your local setup that might be helpful in troubleshooting.
    * Detailed steps to reproduce the bug.


Feature requests and feedback
=============================

The best way to send feedback is to file an issue at https://github.com/NREL/python-geophires-x/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that code contributions are welcome :)
