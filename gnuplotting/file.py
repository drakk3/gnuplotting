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

from .platform import map
from .context import GnuplotContext


class GnuplotFile(GnuplotContext):

    def __init__(self, backend, mode='w+b', encoding='utf-8', **kwargs):
        super(GnuplotFile, self).__init__()
        if isinstance(backend, str):
            self.__backend = open(backend, mode=mode, encoding=encoding,
                                  **kwargs)
        elif isinstance(backend, int):
            self.__backend = os.fdopen(backend, mode=mode, encoding=encoding,
                                       **kwargs)
        elif not (hasattr(backend, 'write') and \
                  hasattr(backend, 'flush') and \
                  hasattr(backend, 'close')):
            raise TypeError("'backend' argument must be a file-like object, "
                            "given {}".format(backend))
        else:
            self.__backend = backend
        if not hasattr(self.__backend, 'encoding'):
            self.__encode = lambda s: s.encode(encoding)
        else:
            self.__encode = lambda s: s
        self.supportsTimeout = lambda: False
        self.send = self.write

    def terminate(self):
        self.close()
        return super(GnuplotFile, self).terminate()
    
    def close(self):
        self.__backend.close()

    def write(self, lines, **ignored):
        map(lambda line: self.__backend.write(self.__encode(line + os.linesep)),
            lines)
        self.__backend.flush()
