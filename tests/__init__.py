#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Copyright (C) 2017-2018 Romain CHÂTEL <rchastel@protonmail.com>
# This file is part of Newplot.
#
# Newplot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Newplot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Newplot.  If not, see <http://www.gnu.org/licenses/>.


import os
import sys
import glob
import inspect
import doctest
import unittest
import importlib


TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.dirname(TESTS_ROOT)


class TestNode(unittest.TestSuite):

    def __init__(self, tests=(), prefix=''):
        super(TestNode, self).__init__(tests)
        self.prefix = prefix + '.' if prefix else ''    

    def __getattr__(self, name):
        def match_end(s):
            return len(s) == 0 or s.startswith('.')
        search = self.prefix + name
        query = [test for test in self \
                 if test.id().startswith(search) and \
                    match_end(test.id()[len(search):])]
        if query:
            return TestNode(query, self.prefix + name)
        else:
            raise ValueError('Can\'t find tests for {}'.format(name))


class TestGraph(TestNode):

    def __init__(self, package_name, test_pattern):
        super(TestGraph, self).__init__(prefix=package_name)
        test_paths = glob.iglob(os.path.join(package_name, test_pattern))
        test_paths = (test_path.replace('.py', '') for test_path in test_paths)
        test_module_path_by_names = \
            (test_path.replace(os.sep, '.') for test_path in test_paths)
        test_modules = (importlib.import_module(mod_path, package_name) \
                        for mod_path in test_module_path_by_names)
        test_modules = (mod for mod in test_modules \
                        if inspect.getsource(mod).find('"""') > -1)
        for mod in test_modules:
            try:
                self.addTests(doctest.DocTestSuite(module=mod))
            except ValueError:
                pass


def load_tests(loader=None, test=None, pattern=None):
    if not ROOT in sys.path:
            sys.path.append(ROOT)
    newplot = 'newplot'
    return TestGraph(newplot, '**.py')
  
doctests = load_tests()

if __name__ == '__main__':

    unittest.main()
