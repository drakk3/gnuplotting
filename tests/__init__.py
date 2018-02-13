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
import inspect
import doctest
import unittest
import importlib

from gnuplotting.variable import Namespace

TESTS_ROOT = os.path.abspath(os.path.dirname(__file__))
ROOT = os.path.dirname(TESTS_ROOT)

class TestNamespace(Namespace, unittest.TestSuite):
    """A testsuite where subtests are reachable from attributes

    ex:
       self.process : the process module test suite
       self.process.GnuplotProcess : the GnuplotProcess class test suite
       self.process.GnuplotProcess.wait : the wait method test suite
    """
    def __init__(self, rel_path):
        super(TestNamespace, self).__init__(__rel_path=rel_path)

    
    def addTest(self, test):
        prefix_len = len(self.__rel_path)+1
        test_id = test.id()
        test_rel_id = test_id[prefix_len:]
        id_parts = test_rel_id.split('.')
        id_prefix = id_parts[0]
        if id_prefix in self:
            self[id_prefix].addTest(test)
        elif id_prefix == test_rel_id:
            self[id_prefix] = unittest.TestSuite([test])
        else:
            self[id_prefix] = TestNamespace(test_id[:prefix_len+len(id_prefix)])
            self[id_prefix].addTest(test)

    def addTests(self, tests):
        for test in tests:
            self.addTest(test)

    def countTestCases(self):
        acc = 0
        for k, v in self.items():
            if isinstance(v, TestNamespace):
                acc += v.countTestCases()
            else:
                acc += 1
        return acc

    def run(self, result):
        for k, v in self.items():
            v.run(result)
        return result

    def debug(self):
        for k, v in self.items():
            v.debug()

def load_tests(loader=None, test=None, pattern=None):
    if not ROOT in sys.path:
            sys.path.append(ROOT)
    gnuplotting = 'gnuplotting'
    test_paths = glob.iglob(os.path.join(gnuplotting, '**.py'))
    test_paths = (test_path.replace('.py', '') \
                  for test_path in test_paths)
    test_module_path_by_names = \
                ((os.path.basename(test_path.replace(os.sep + '__init__', '')),
                  test_path.replace(os.sep, '.')) for test_path in test_paths)
    test_modules = ((mod_name,
                     importlib.import_module(mod_path, gnuplotting)) \
                        for mod_name, mod_path in test_module_path_by_names)
    test_modules = ((mod_name, mod) for mod_name, mod in test_modules \
                    if inspect.getsource(mod).find('"""') > -1)
    doctests = TestNamespace(gnuplotting)
    for name, test_mod in test_modules:
        test_suite = doctest.DocTestSuite(module=test_mod)
        doctests.addTests(test_suite)
    return doctests

doctests = load_tests()

if __name__ == '__main__':

    unittest.main()
