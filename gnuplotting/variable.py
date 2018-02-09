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


from .utils import isfloat
from .platform import map


class GnuplotDefinable(object):

    def __init__(self, context):
        super(GnuplotDefinable, self).__init__()
        self.__context = context

    def define(self, name, value):
        raise NotImplementedError

    def _define(self, expr):
        self.__context.cmd(expr)
    
    def _eval(self, name, expr):
        value = self.__context.cmd('if(exists("{name}")) printerr {expr}' \
                                   .format(name=name, expr=expr))
        if value:
            if value.isdigit():
                return int(value)
            elif isfloat(value):
                return float(value)
            return value
        return None


class GnuplotFun(GnuplotDefinable):

    def __init__(self, context, args, body):
        super(GnuplotFun, self).__init__(context)
        self.__args = args
        self.__body = body
        self.__name = None

    arity = property(lambda self: len(self.__args))

    def define(self, name, value):
        self._define(name + '(' + ', '.join(map(str, self.__args)) + ') = ' + \
                     self.__body)
        self.__name = name

    def __call__(self, *args):
        return self._eval('GPFUN_' + self.__name, '{name}({args})' \
                          .format(name=self.__name,
                                  args=', '.join(map(str, args))))
        

class GnuplotVar(GnuplotDefinable):

    def __init__(self, context):
        super(GnuplotVar, self).__init__(context)
        self.__name = None

    def define(self, name, value):
        self._define(name + ' = ' + str(value))
        self.__name = name

    def __call__(self):
        return self._eval(self.__name, self.__name)             
        
    
class GnuplotVarContext(object):
    """A Context that manages the access of Gnuplot variables and functions

    :param context:
        :type: `GnuplotContext`
        The enclosing Gnuplot context

    Example :
    
    >>> from .gnuplot import Gnuplot
    >>> with Gnuplot() as gp:
    ...     gp.vars.max = 99                          # define 'max' variable
    ...     print(gp.vars.max())                      # retrieve 'max' value
    ...     gp.vars.f = gp.function(['x'], 'x + 1')   # define 'f(x)' function
    ...     print(gp.vars.f.arity)
    ...     print(gp.vars.f(1))                       # evaluate 'f(1)'
    ...     gp.vars.max = 10.0                        # set 'max' value to 10
    ...     print(gp.vars.max())                      # retrieve 'max' new value
    ...     print(gp.vars.f(10))                      # evaluate 'f(10)'
    ...     gp.vars.max = None                        # undefine 'max'
    99
    1
    2
    10.0
    11
    
    """
    __PRIVATE_PREFIX = '_GnuplotVarContext'

    def __init__(self, context):
        super(GnuplotVarContext, self).__init__()
        self.__context = context
    
    def __setattr__(self, name, value):
        if name.startswith(self.__PRIVATE_PREFIX):
            self.__dict__[name] = value
        else:
            if value is None:
                self.__context.cmd('undefine ' + name)
                self.__dict__.pop(name)
            else:
                if isinstance(value, GnuplotFun):
                    obj = value
                else:
                    obj = GnuplotVar(self.__context)
                obj.define(name, value)
                self.__dict__[name] = obj
    
    def clear(self):
        todo = []
        for name, obj in self.__dict__.items():
            if not name.startswith(self.__PRIVATE_PREFIX):
                todo.append(name)
        self.__context.send(map(lambda e: self.__dict__.pop(e) and \
                                          'undefine ' + e, todo))


