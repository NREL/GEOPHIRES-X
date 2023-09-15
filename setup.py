#!/usr/bin/env python
import re
from pathlib import Path

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with Path(__file__).parent.joinpath(*names).open(encoding=kwargs.get('encoding', 'utf8')) as fh:
        return fh.read()


setup(
    name='geophires-x',
    version='1.3.0',
    license='MIT',
    description='Distributable python package version of https://github.com/malcolm-dsider/GEOPHIRES-X',
    long_description='{}\n{}'.format(
        re.compile('^.. start-badges.*^.. end-badges', re.M | re.S).sub('', read('README.rst')),
        re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst')),
    ),
    author='softwareengineerprogrammer',
    author_email='4056124+softwareengineerprogrammer@users.noreply.github.com',
    url='https://github.com/softwareengineerprogrammer/python-geophires-x',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[path.stem for path in Path('src').glob('*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        # uncomment if you test on these interpreters:
        # "Programming Language :: Python :: Implementation :: IronPython",
        # "Programming Language :: Python :: Implementation :: Jython",
        # "Programming Language :: Python :: Implementation :: Stackless",
        'Topic :: Utilities',
        'Private :: Do Not Upload',
    ],
    project_urls={
        'Changelog': 'https://github.com/softwareengineerprogrammer/python-geophires-x/blob/master/CHANGELOG.rst',
        'Issue Tracker': 'https://github.com/softwareengineerprogrammer/python-geophires-x/issues',
    },
    keywords=[
        # eg: "keyword1", "keyword2", "keyword3",
    ],
    python_requires='>=3.7',
    install_requires=[
        'numpy',
        'numpy-financial',
        'pint',
        'forex_python',
        'jsons',
        'mpmath',
        'deepdiff',
        'mysql.connector',
        'cryptography',
        # Used by Adv*/AGS extensions but break tox pypy jobs
        #'h5py',
        #'scipy',
    ],
    extras_require={
        # eg:
        #   "rst": ["docutils>=0.11"],
        #   ":python_version=="2.6"": ["argparse"],
    },
)
