#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2017-2018 Romain CHÂTEL <rchastel@protonmail.com>
# This file is part of Gnuplotting.
#
# Gnuplotting is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Gnuplotting is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Gnuplotting.  If not, see <http://www.gnu.org/licenses/>.


"""Setup script for the gnuplotting module distribution."""

import os

from setuptools import find_packages, setup, Command

from gnuplotting.__init__ import __version__

# Package meta-data.
NAME = 'gnuplotting'
DESCRIPTION = 'Gnuplotting is a Python 2-way wrapper around the gnuplot program.'
URL = 'https://github.com/drakk3/gnuplotting.git'
EMAIL = 'rchastel@protonmail.com'
AUTHOR = 'Romain CHÂTEL'
REQUIRED = []
ROOT = os.path.abspath(os.path.dirname(__file__))
LONG_DESCRIPTION = ''
with open(os.path.join(ROOT, 'README.org'), 'r') as f:
    LONG_DESCRIPTION = os.linesep + f.read()

setup(
    name=NAME,
    version=__version__,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    license='GPLv3+',
    packages=find_packages(exclude=('tests',)),
    install_requires=REQUIRED,
    include_package_data=True,
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
    ],
    test_suite='tests.doctests.alltests',
)

