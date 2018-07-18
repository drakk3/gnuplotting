# -*- coding: utf-8 -*-

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

from __future__ import print_function

import sys
import inspect
import itertools
import functools

IS_PYTHON2 = sys.version < '3'

# Normalize some function across the different Python version
if IS_PYTHON2:
    unicode = unicode
    map = itertools.imap
    reduce = reduce
else:
    unicode = str
    map = map
    reduce = functools.reduce
_inspect = inspect
inspect = type('INSPECT', (object,),
               {'isgenerator': lambda self, fun: _inspect.isgenerator(fun),
                'getargspec': lambda self, fun: _inspect.getargspec(fun) \
                                  if IS_PYTHON2 \
                                  else _inspect.getfullargspec(fun)})()

def with_metaclass(metaclass, *bases):
    """A python 2/3 metaclass generator"""
    class _type(type):
        def __new__(cls, name, _, d):
            return metaclass(name, bases, d)

        @classmethod
        def __prepare__(cls, name, _):
            return metaclass.__prepare__(name, bases)
    return type.__new__(_type, 'Meta23', (), {})

if sys.platform.startswith('linux'):
    DEFAULT_GNUPLOT_CMD = 'gnuplot'
    SHOW_PROMPT = 'printf "[%s@%s:%s]$ " "${USER}" "${HOSTNAME%%.*}" "${PWD/#$HOME/\~}"'

elif sys.platform.startswith('win32') or sys.platform.startswith( 'cli'):
    DEFAULT_GNUPLOT_CMD = 'wgnuplot_pipes.exe'
    SHOW_PROMPT = 'echo %PROMPT%'

elif sys.platform.startswith('cygwin'):
    DEFAULT_GNUPLOT_CMD = 'wgnuplot_pipes.exe'
    SHOW_PROMPT = 'echo %PROMPT%'

elif sys.platform.startswith('darwin'):
    DEFAULT_GNUPLOT_CMD = 'gnuplot'
    SHOW_PROMPT = 'printf "[%s@%s:%s]$ " "${USER}" "${HOSTNAME%%.*}" "${PWD/#$HOME/\~}"'
