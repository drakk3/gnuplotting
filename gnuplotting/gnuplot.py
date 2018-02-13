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
import time
from collections import OrderedDict

from . import file as gfile
from . import process as gprocess
from .platform import DEFAULT_GNUPLOT_CMD

# Copied from https://stackoverflow.com/questions/377017#377028 
def _which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def Gnuplot(backend=DEFAULT_GNUPLOT_CMD, **kwargs):
    """

    Examples:

    >>> with Gnuplot() as gp:
    ...     gp.cmd('set term qt')
    ...     gp.cmd('plot sin(x)')
    ...     gp.cmd('set term qt 0 close')
    ...     gp.isinteractive
    ...
    True

    >>> import tempfile as tmp
    >>> with Gnuplot(tmp.TemporaryFile(prefix='gnuplot-', suffix='.gp')) as gp:
    ...     gp.cmd('set term qt 0')
    ...     gp.cmd('plot sin(x)')
    ...     gp.isinteractive
    False

    """
    if isinstance(backend, str):
        _backend = _which(backend)
        if _backend:
            return gprocess.GnuplotProcess(_backend, **kwargs)
    return gfile.GnuplotFile(backend, **kwargs)
