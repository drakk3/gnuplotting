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


import sys
import inspect
import itertools
import functools

IS_PYTHON2 = sys.version < '3'

# Normalize some function across the different Python version
if IS_PYTHON2:
    map = itertools.imap
    reduce = reduce
else:
    map = map
    reduce = functools.reduce
_inspect = inspect
inspect = type('INSPECT', (object,),
               {'isgenerator': lambda self, fun: _inspect.isgenerator(fun),
                'getargspec': lambda self, fun: inspect.getargspec(fun) \
                                  if IS_PYTHON2 \
                                  else _inspect.getfullargspec(fun)})()

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
