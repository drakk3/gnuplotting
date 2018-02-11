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
from .platform import map, print_function


class GnuplotDefinable(object):
    def __init__(self, ns):
        super(GnuplotDefinable, self).__init__()
        self.__name = None
        self.__ns = ns
    ns = property(lambda self: self.__ns)

    @property
    def gnuplot_id(self):
        return self.__name

    @property
    def qualname(self):
        return self.__name

    def destroy(self):
        self.__ns.undefine(self.name, self.gnuplot_id)
        self.__ns = None

    @property
    def expr(self):
        raise NotImplementedError

    def __setName(self, name):
        self.__name = name
        self.__ns.define(self.qualname, self.expr)

    name = property(lambda self: self.__name, __setName)


class GnuplotFunction(GnuplotDefinable):
    def __init__(self, ns, args, body):
        super(GnuplotFunction, self).__init__(ns)
        self.__args = args
        self.__body = str(body)
        self.__arity = len(args)

    arity = property(lambda self: self.__arity)

    def __formatArgs(self, args):
        return ', '.join(map(str, args))

    @property
    def gnuplot_id(self):
        return 'GPFUN_' + self.name

    @property
    def qualname(self):
        return self.name + '(' + self.__formatArgs(self.__args) + ')'

    @property
    def expr(self):
        return self.__body

    def __call__(self, *args):
        expr = self.name + '(' + self.__formatArgs(args) + ')'
        return self.ns.eval(self.gnuplot_id, expr)

    def pack(self, *args):
        return self.name + '(' + self.__formatArgs(args) + ')'

    def __getitem__(self, args):
        return self.pack(*args)


class GnuplotVariable(GnuplotDefinable):
    def __init__(self, ns, value):
        super(GnuplotVariable, self).__init__(ns)
        self.__value = value

    @property
    def expr(self):
        return str(self.__value)

    def __get__(self, instance, owner=None):
        return self.__value


class Namespace(dict):

    def __init__(self, **kwargs):
        super(Namespace, self).__init__()
        for name, value in kwargs.items():
            if name.startswith('__') and not name.endswith('__'):
                name = '_' + type(self).__name__ + name
            super(Namespace, self).__setattr__(name, value)

    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        if name in self:
            obj = self[name]
            if hasattr(obj, '__get__'):
                return obj.__get__(self, None)
            return obj
        raise AttributeError("%s has no attribute %s" % \
                             (type(self).__name__, name))
    

class GnuplotNamespace(Namespace):
    """A Context that manages the access of Gnuplot variables and functions

    :param context:
        :type: `GnuplotContext`
        The enclosing Gnuplot context

    Example :
    
    >>> from .gnuplot import Gnuplot
    >>> with Gnuplot() as gp:
    ...     gp.vars.max = 99                          # define 'max' variable
    ...     print(gp.vars.max)                        # retrieve 'max' value
    ...     gp.vars.f = gp.function(['x'], 'x + 1')   # define 'f(x)' function
    ...     print(gp.vars.f.arity)
    ...     print(gp.vars.f.gnuplot_id)
    ...     print(gp.vars.f(1))                       # evaluate 'f(1)'
    ...     gp.vars.max = 10.0                        # set 'max' value to 10
    ...     print(gp.vars.max)                        # retrieve 'max' new value
    ...     print(gp.vars.f(10))                      # evaluate 'f(10)'
    ...     gp.vars.max = None                        # undefine 'max'
    ...     try:
    ...         gp.vars.max
    ...     except AttributeError as e:
    ...         pass
    ...     else:
    ...         raise AssertionError("'max' should be undefined")
    99
    1
    GPFUN_f
    2
    10.0
    11

    """
    def __init__(self, context):
        super(GnuplotNamespace, self).__init__(__context=context)

    def __setattr__(self, name, value):
        if value is None:
            if name in self:
                self.pop(name).destroy()
        else:
            obj = value
            if not isinstance(value, GnuplotDefinable):
                obj = GnuplotVariable(self, value)
            obj.name = name
            super(GnuplotNamespace, self).__setattr__(name, obj)
                
    def eval(self, name, expr):
        value = self.__context.cmd('if(exists("{name}")) printerr {expr} ; ' \
                                   'else printerr "    line 0: \'{name}\' is not '
                                   'defined'.format(name=name, expr=expr))
        if value:
            if value.isdigit():
                return int(value)
            elif isfloat(value):
                return float(value)
            return value
        return None

    def define(self, name, expr):
        self.__context.cmd(name + ' = ' + expr)

    def undefine(self, name, gnuplot_id):
        self.__context.cmd('undefine ' + gnuplot_id)
        self.pop(name, None)

    
    def clear(self, timeout=-1):
        self.__context.send(map(lambda e: self.pop(e[0]) and \
                                          'undefine ' + e[1].gnuplot_id,
                                self.items()),
                            timeout=timeout)


