============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Don't hesitate

Development
===========

To set up GEOPHIRES-X for local development:

1. Fork NREL/python-geophires-x on GitHub by going to https://github.com/NREL/python-geophires-x/fork

2. Enable Actions on your fork on GitHub in your fork's Actions tab

3. Enable Pages on your fork on GitHub by going to Settings tab → Pages -> Build and deployment → Set Source to "GitHub Actions"

4. Clone your fork locally in a terminal::

    cd some/path/where-you-have-your-code-projects
    git clone git@github.com:<your GitHub username>/python-geophires-x.git
    cd python-geophires-x

Local Setup
-----------

Prerequisite: Follow fork & clone instructions above.

Strongly recommended: use a Python IDE such as `PyCharm <https://www.jetbrains.com/pycharm/>`__

If you are using PyCharm, first open the the cloned repo by going to File → Open and selecting your ``python-geophires-x`` directory (from the previous steps).
Run commands in a terminal with View → Tool Windows → Terminal

1. `Install virtualenv <https://virtualenv.pypa.io/en/latest/installation.html#via-pip>`__ if you don't have it already. Then set up and activate a virtual environment for the project::

    python -m venv venv
    source venv/bin/activate

(If you are using PyCharm, it may prompt you to set up the virtual environment automatically, allowing you to skip this step on the command line)

2. Install package dependencies (from ``setup.py``)::

    pip install -e .

(PyCharm may prompt you to install dependencies, making this step unnecessary to run on the command line)

3. `Download pre-commit <https://pre-commit.com/>`_ if you don't already have it. Then run the command to configure it for the project (somewhat confusingly also called ``install``)::

    pre-commit install

You're now ready to start making changes and committing them.

4. To commit changes locally::

    git add .
    git commit -m "Your detailed description of your changes."

Note that ``pre-commit`` will run when you run ``git commit``. If your code does not pass automated checks you will have to
add fixed files (or manually fix in some cases). Example::

        (venv) ➜  python-geophires-x git:(main) ✗ git commit -m "Use __future__ annotations to allow type union syntax in HIP_RA.py"
        ruff.....................................................................Passed
        black....................................................................Failed
        - hook id: black
        - files were modified by this hook

        reformatted src/hip_ra/HIP_RA.py

        All done! ✨ 🍰 ✨
        1 file reformatted.

        trim trailing whitespace.................................................Passed
        fix end of files.........................................................Passed
        debug statements (python)................................................Passed
        (venv) ➜  python-geophires-x git:(main) ✗ git add src/hip_ra/HIP_RA.py && git commit -m "Use __future__ annotations to allow type union syntax in HIP_RA.py"
        ruff.....................................................................Passed
        black....................................................................Passed
        trim trailing whitespace.................................................Passed
        fix end of files.........................................................Passed
        debug statements (python)................................................Passed
        [main 8834d58] Use __future__ annotations to allow type union syntax in HIP_RA.py
         1 file changed, 4 insertions(+), 2 deletions(-)


5. Verify that tests pass with your changes. In PyCharm, you can run unit tests by right-clicking the ``tests/`` folder and selecting "Run 'Python tests in tests'".
If you want to be extra thorough you can `run tox locally <#Tox-tests>`_ but in general it is more practical to run unit tests in PyCharm locally and then let GitHub Actions on your fork run the full ``tox`` suite.

6. Push your changes to your fork::

    git push

Then, verify that Actions pass on your commit(s) on GitHub

6. Submit a pull request through the GitHub website following `the guidelines <#Pull-Request-Guidelines>`_.

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code you can make the pull request and set it as a draft.

For merging, you should:

1. Ensure Actions are passing on your fork. Actions will also be automatically run when you create a PR, and they will need to be passing as a requirement to merge.
2. Add unit test coverage
3. Strive to write clean, self-documenting code. Update documentation which cannot be adequately self-documented.
4. Add yourself to `AUTHORS.rst <AUTHORS.rst>`__.
5. Major changes may merit a mention in `CHANGELOG.rst <CHANGELOG.rst>`__

Tox tests
---------

To run all the ``tox`` tests locally::

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


To run a subset of tests::

    tox -e envname -- pytest -k test_myfeature

To run all the test environments in *parallel*::

    tox -p auto


Test Configuration in VS Code
-----------------------------

``.vscode/settings.json``:

.. code-block::

 {
    "python.defaultInterpreterPath": ".tox/py311/bin/python",
    "python.testing.unittestEnabled": false,
    "python.testing.unittestArgs": [
        "-v",
        "-s",
        "-p",
        "test_*.py"
    ],
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "-c",
        "pytest.ini",
        "--no-cov"
    ],
    "python.analysis.enablePytestExtra": true,
    "python.languageServer": "Pylance",
   }




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

Tips
----

A working understanding of `git <https://git-scm.com/>`_ is one of the most beneficial skills you can have when working on software, even if you are not a software engineer.
Although most modern IDEs now provide a reasonable GUI for working with git, learning and using git on the command line is often the most effective way
to become proficient. This is not an easy skill to learn for most, and there is no one tutorial that will substitute for real-world experience.
However the following tutorials may be a good place to start:

- https://docs.gitlab.com/ee/gitlab-basics/start-using-git.html
- https://githubtraining.github.io/training-manual/#/04_branching_with_git
