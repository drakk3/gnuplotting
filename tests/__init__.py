#!/usr/bin/env python
#-*- coding: utf-8 -*-

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


import os
import sys
import glob
import doctest
import unittest
import importlib

TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.dirname(TESTS_ROOT)

            

def load_tests(loader=None, test=None, pattern=None):
    if not ROOT in sys.path:
            sys.path.append(ROOT)
    gnuplotting = 'gnuplotting'
    test_paths = glob.iglob(os.path.join(gnuplotting, '**.py'),
                            recursive=True)
    test_paths = (test_path.replace('.py', '') \
                  for test_path in test_paths)
    test_module_path_by_names = \
                ((os.path.basename(test_path.replace(os.sep + '__init__', '')),
                  test_path.replace(os.sep, '.')) for test_path in test_paths)
    test_modules = ((mod_name,
                     importlib.import_module(mod_path, gnuplotting)) \
                        for mod_name, mod_path in test_module_path_by_names)
    tests = {test_mod_name: doctest.DocTestSuite(module=test_mod) \
             for test_mod_name, test_mod in test_modules}
    doctests_dict = {name: unittest.TestSuite([test]) \
                     for name, test in tests.items()}
    doctests_dict['alltests'] = unittest.TestSuite(tests.values())
    doctests = type('Doctests', (unittest.TestSuite,), doctests_dict)()
    doctests.addTest(doctests_dict['alltests'])
    return doctests

doctests = load_tests()

if __name__ == '__main__':

    unittest.main()
