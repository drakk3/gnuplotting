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
    """An abstract class for gnuplot values than can be created and accessed
    from Python

    :param ns:
        :type: `GnuplotNamespace`
        The namespace where the value live

    :attr gnuplot_id:
        :type: `str`
        Value ID given by Gnuplot
    :attr name:
        :type; `str`
        Value name in the namespace
    :attr qualname:
        :type: `str`
        Value qualified name, for variable it equals to `name`. For function it
        equals to `name`(`args ...`)
    :attr expr:
        :type: `str`
        Definition expression of this value.

    """
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
        """Delete `self` from it's namespace and Gnuplot"""
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
    """A Gnuplot function defined in Python

    :param ns:
        :type: `GnuplotFunctionNamespace`
        The namespace where live this function

    :attr arity:
        :type: `int`
        Arity of this function

    """
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
        """Tells Gnuplot to evaluate this function

        :param args:
            :type: `iterable`
            Call arguments

        :returns:
            The evaluation of this function agains the given arguments

        """
        expr = self.name + '(' + self.__formatArgs(args) + ')'
        return self.ns.eval(self.gnuplot_id, expr)

    def pack(self, *args):
        """Return the expression that packs the given args into a call to `self`

        :param args:
            :type: `iterable of str`
            The name of the arguments to pack into a call expression
        :returns:
            the call expression

        Example:
        if self.name = 'f' and args = ('x', 'y', 'z') returns 'f(x, y, z)'
        This is useful when calling a function with different argument names
        than those used in the definition.

        """
        return self.name + '(' + self.__formatArgs(args) + ')'

    def __getitem__(self, args):
        """A shorthand and syntactic sugar for pack

        .. see::
            `GnuplotFunction.pack`

        Example:
        f.pack('x', 'y', 'z') --> 'f(x, y, z)'

        """
        return self.pack(*args)


class GnuplotVariable(GnuplotDefinable):
    """A Gnuplot variable accessible from Python"""
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
    """A namespace that manages access to Gnuplot variables and functions

    :param context:
        :type: `GnuplotContext`
        The enclosing Gnuplot context

    Example :
    
    >>> from .gnuplot import Gnuplot
    >>> with Gnuplot() as gp:
    ...     gp.vars.max = 99                          # define 'max' variable
    ...     print(gp.vars.max)                        # retrieve 'max' value
    ...     gp.funs.f = gp.function(['x'], 'x + 1')   # define 'f(x)' function
    ...     print(gp.funs.f.arity)
    ...     print(gp.funs.f.gnuplot_id)
    ...     print(gp.funs.f(1))                       # evaluate 'f(1)'
    ...     gp.vars.max = 10.0                        # set 'max' value to 10
    ...     print(gp.vars.max)                        # retrieve 'max' new value
    ...     print(gp.funs.f(10))                      # evaluate 'f(10)'
    ...     print(gp.funs.f['a', 'b'])
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
    f(a, b)

    """
    def __init__(self, context):
        super(GnuplotNamespace, self).__init__(_GnuplotNamespace__context=context)

    
    def __setattr__(self, name, value):
        if value is None:
            if name in self:
                self.pop(name).destroy()
        else:
            value.name = name
            super(GnuplotNamespace, self).__setattr__(name, value)
                
    def eval(self, name, expr):
        """Evaluate an expression inside Gnuplot

        :param name:
            :type: `str`
            Name of the value to evaluate
        :param expr:
            :type: `str`
            Expression to evaluate

        :returns:
            The evaluation's result

        """
        value = self.__context.cmd('if(exists("{name}")) printerr {expr} ; ' \
                                   'else printerr "    line 0: \'{name}\' is ' \
                                   'not defined'.format(name=name, expr=expr))
        if value:
            if value.isdigit():
                return int(value)
            elif isfloat(value):
                return float(value)
            return value
        return None

    def define(self, name, expr):
        """Define a value in Gnuplot

        :param name:
            :type: `str`
            Name of the value to define
        :param expr:
            :type: `str`
            The definition expression

        """
        self.__context.cmd(name + ' = ' + expr)

    def undefine(self, name, gnuplot_id):
        """Undefine a value in Gnuplot

        The value is removed from Gnuplot and it's namespace

        :param name:
            :type: `str`
            Name of the value to delete
        :param gnuplot_id:
            :type: `str`
            It's Gnuplot ID

        """
        self.__context.cmd('undefine ' + gnuplot_id)
        self.pop(name, None)

    def clear(self, timeout=-1):
        """Clear the namespace

        :param timeout:
            :type: `Number or None`
            Number of seconds to wait for a Gnuplot response, defaults to
            `GnuplotContext.defaultTimeout`

        """
        self.__context.send(map(lambda e: 'undefine ' + e[1].gnuplot_id,
                                self.items()),
                            timeout=timeout)
        super(GnuplotNamespace, self).clear()

class GnuplotVariableNamespace(GnuplotNamespace):
    """A Gnuplot namespace that holds variables"""
    def __init__(self, context):
        super(GnuplotVariableNamespace, self).__init__(context)

    def __setattr__(self, name, value):
        if value is not None and not isinstance(value, GnuplotDefinable):
            value = GnuplotVariable(self, value)
        if not isinstance(value, (GnuplotVariable, type(None))):
            raise TypeError('This namespace is reserved for variable '
                            'definitions, given {}'.format(type(value)))
        super(GnuplotVariableNamespace, self).__setattr__(name, value)


class GnuplotFunctionNamespace(GnuplotNamespace):
    """A Gnuplot namespace that holds functions"""
    def __init__(self, context):
        super(GnuplotFunctionNamespace, self).__init__(context)

    def __setattr__(self, name, value):
        if value and not isinstance(value, GnuplotFunction):
            raise TypeError('This namespace is reserved for function '
                            'definitions, given {}'.format(type(value)))
        super(GnuplotFunctionNamespace, self).__setattr__(name, value)
