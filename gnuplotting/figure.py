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
from .multithreading import LockedGenerator
from .errors import GnuplotError, GnuplotTimeoutError
from .utils import CallableGenerator


class GnuplotFigure(object):

    __uniqueId = CallableGenerator(LockedGenerator(itertools.count(0, 1)))
    __protected_settings = frozenset(('term', 'terminal', 'termoption',
                                      'title', 'output', 'size'))
    __term_desc_prefix = 'terminal type is '

    def __init__(self, context, term=None, id=None, title=None, size=None,
                 options=None, output=None): 
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
        self.__size = size
        self.__settings = []
        self.__plots = []
        self.__splots = []
        self.reset()

    def setTitle(self, title):
        self.__title = title

    def setOptions(self, options):
        self.__options = options

    def setOutput(self, output):
        self.__output = output

    def setSize(self, size):
        self.__size = size

    title = property(lambda self: self.__title, setTitle)
    options = property(lambda self: self.__options, setOptions)
    output = property(lambda self: self.__output, setOutput)
    size = property(lambda self: self.__size, setSize)
    id = property(lambda self: self.__id)
    term = property(lambda self: self.__term)

    def set(self, setting, *args):
        if setting in self.__protected_settings:
            raise TypeError("'%s' can't be set this way, please use the `title`"
                            ", `options`, `size` and `output` properties, their"
                            "setters or create a new Figure.")
        self.__unsafeSet(setting, *args)

    def __unsafeSet(self, setting, *args):
        _args = tuple(itertools.takewhile(lambda arg: not arg is None, args))
        cmd = 'unset' if len(_args) != len(args) else 'set'
        _args = (setting,) + _args
        self.__settings.append('{} {}'.format(cmd, ' '.join(map(str, _args))))

    def reset(self):
        self.flush()
        self.__settings.append('reset')
        self.__unsafeSet('term', self.__term, str(self.__id))
        if self.__size:
            self.__unsafeSet('size', ', '.join(map(str, self.__size)))
        if self.__options:
            for opt in self.__options:
                self.__unsafeSet('termoption', opt)
        if self.__output: self.__unsafeSet('output', '"' + self.__output + '"')
        if self.__title: self.__unsafeSet('title', '"' + self.__title + '"')

    def flush(self, settings=True, plots=True, splots=True):
        if settings: del self.__settings[:]
        if plots: del self.__plots[:]
        if splots: del self.__splots[:]

    def __plotElement(self, i, data, elem_args, global_args):
        _for = elem_args.pop('_for', global_args.get('_for', None))
        _range = elem_args.pop('sampling_range',
                              global_args.get('sampling_range', None))
        axes = elem_args.pop('axes', global_args.get('axes', None))
        _with = elem_args.pop('_with', global_args.get('_with', None))
        using = elem_args.pop('using', global_args.get('using', None))
        title = elem_args.pop('title', global_args.get('title', None))
        _for = 'for {} '.format(_for) if (_for and i == 0) else ''
        _range = 'sample {} '.format(_range) \
                 if (_range and i == 0 and len(self.__plots) == 0) \
                    else (_range + ' ' if _range else '')
        axes = 'axes {} '.format(axes) if axes else ''
        using = 'using {} '.format(using) if using else ''
        _with = 'with {} '.format(_with) if _with else ''
        title = 'title "{}"'.format(title) if title else ''
        return _for + _range + data + ' ' + axes + using + _with + title

    def __addPlot(self, plot_list, *datas, **kwargs):
        iterator = lambda: (i for i in range(len(datas)))
        plot_list.extend(map(lambda i, data, data_args:
                             self.__plotElement(i, data, data_args, kwargs),
                             iterator(),
                             (datas[i][0] if isinstance(datas[i], tuple) \
                              else datas[i] for i in iterator()),
                             (datas[i][1] if isinstance(datas[i], tuple) \
                              else {} for i in iterator())))

    def plot(self, *datas, **kwargs):
        self.__addPlot(self.__plots, *datas, **kwargs)
    
    def splot(self, *datas, **kwargs):
        self.__addPlot(self.__splots, *datas, **kwargs)    

    def wait(self, timeout=None):
        wait_evt = (self.__term + '_' + str(self.__id), 'Close')
        self.__context.wait((wait_evt,), timeout=timeout)

    def submit(self, wait=False, timeout=-1,
               flush_settings=True, flush_plots=True, flush_splots=True,
               reset=False):
        plotLine = ('plot ' + ', '.join(self.__plots),) if self.__plots else ()
        splotLine = ('splot ' + ', '.join(self.__splots),) \
                    if self.__splots else ()
        self.__context.cmd('set term push', timeout=self.__context.NO_WAIT)
        res = None
        try:
            res = self.__context.send(itertools.chain(self.__settings,
                                                      plotLine, splotLine),
                                      timeout=timeout)
            if wait: self.wait(wait if not isinstance(wait, bool) else None)
            self.flush(flush_settings, flush_plots, flush_splots)
            if reset: self.reset()
        finally:
            self.__context.cmd('set term pop', timeout=self.__context.NO_WAIT)
        return res
