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


import itertools

from .platform import map
from .errors import GnuplotError, GnuplotTimeoutError
from .utils import CallableGenerator, LockedGenerator

class GnuplotFigure(object):

    __uniqueId = CallableGenerator(LockedGenerator(itertools.count(0, 1)))
    __forbidden_settings = frozenset(('term', 'terminal', 'termoption',
                                      'title', 'output'))
    __term_desc_prefix = 'terminal type is '

    def __init__(self, context, id=None, title=None,
                 term=None, options=None, output=None): 
        super(GnuplotFigure, self).__init__()
        self.__context = context
        self.__id = id or self.__uniqueId()
        self.__term = term
        # Infer terminal type from the current terminal
        if not self.__term:
            error_msg = "'term' argument could not be infered, " \
                        "please provide one.\nCause: %s"
            try:
                term = self.__context.cmd('show term', timeout=0.1)
                offset = len(self.__term_desc_prefix)
                start = term.find(self.__term_desc_prefix)
                if start > -1:
                    start += offset
                    end = term.find(' ', start)
                    if end > -1:
                        self.__term = term[start:end]
                if not self.__term:
                    raise GnuplotError(error_msg % term)

            except GnuplotTimeoutError as e:
                raise GnuplotError(error_msg % str(e))

        self.__title = title
        self.__options = options
        self.__output = output
        self.__settings = []
        self.__plots = []
        self.reset()

    def setTitle(self, title):
        self.__title = title

    def setOptions(self, options):
        self.__options = options

    def setOutput(self, output):
        self.__output = output

    title = property(lambda self: self.__title, setTitle)
    options = property(lambda self: self.__options, setOptions)
    output = property(lambda self: self.__output, setOutput)
    id = property(lambda self: self.__id)
    term = property(lambda self: self.__term)

    def set(self, setting, *args):
        if setting in self.__forbidden_settings:
            raise TypeError("'%s' can't be set this way, please use the `title`"
                            ", `options` and `output` properties, their setters"
                            " or create a new Figure.")
        self.__unsafeSet(setting, *args)

    def __unsafeSet(self, setting, *args):
        self.__settings.append('set {} {}'.format(setting,
                                                  ' '.join(map(str, args))))

    def unset(self, setting):
        self.__settings.append('unset ' + setting)

    def reset(self):
        self.__settings.clear()
        self.__plots.clear()
        self.__unsafeSet('term', self.__term, str(self.__id))
        self.__settings.append('reset')
        if self.__options:
            for opt in self.__options:
                self.__unsafeSet('termoption', opt)
        if self.__output: self.__unsafeSet('output', '"' + self.__output + '"')
        if self.__title: self.__unsafeSet('title', '"' + self.__title + '"')

    def plot(self, *datas, **kwargs):
        self.__plots.extend(map(lambda data: 'plot ' + data, datas))

    def wait(self, timeout=None):
        wait_evt = (self.__term + '_' + str(self.__id), 'Close')
        self.__context.wait(*(wait_evt,), timeout=timeout)

    def submit(self, wait=False, wait_timeout=None, timeout=-1, reset=False):
        self.__context.cmd('set term push', timeout=self.__context.NO_WAIT)
        try:
            self.__context.send(self.__settings, timeout=timeout)
            self.__context.send(self.__plots, timeout=timeout)
            if wait: self.wait(wait_timeout)
            if reset: self.reset(timeout) 
        finally:
            self.__context.cmd('set term pop', timeout=self.__context.NO_WAIT)
