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


import re
import itertools

from collections import namedtuple

from .utils import isfloat, VOID
from .platform import map, print_function, unicode, with_metaclass


class GnuplotDefinable(object):
    """An abstract class for gnuplot values than can be created and accessed
    from Python

    :param name:
        :type: `str`
        The name of the value

    :attr name:
        :type: `str`
        Value name in the namespace
    :attr gnuplot_id:
        :type: `str`
        Value ID given by Gnuplot

    """
    name = property(lambda self: self.__name)
    gnuplot_id = property(lambda self: self.__name)

    def __init__(self, name):
        self.__name = name

    def cast(self):
        raise NotImplementedError

    def parse(self, s):
        raise NotImplementedError

def _parseGnuplotValue(s):
    if s:
        if s.isdigit():
            return int(s)
        if isfloat(s):
            return float(s)
        return s
    return None

def _GnuplotVariable(name, value):
    def parse_var(s):
        return _GnuplotVariable(name, _parseGnuplotValue(s))
    cls = type(value)
    return type('GnuplotVariable', (GnuplotDefinable, cls),
                {'__init__': lambda self, value: \
                                    GnuplotDefinable.__init__(self, name),
                 'cast': lambda self: cls(self),
                 'parse': classmethod(lambda cls, s: parse_var(s)),
                 'defn': property(lambda self: '{} = {}'\
                                  .format(self.name, str(self)))})(value)


GnuplotFunctionSpec = namedtuple('GnuplotFunctionSpec', ['args', 'body'])
class GnuplotFunction(GnuplotDefinable):
    """A Gnuplot function defined in Python

    :param ns:
        :type: `GnuplotNamespace`
        The namespace where live this function

    :attr arity:
        :type: `int`
        Arity of this function
    :attr defargs:
        :type: `iterable of str`
        Definition list of argument names
    :attr defbody:
        :type: `str`
        Definition body of this function.
    :attr defn:
        :type: `str`
        Definition line of this function

    """
    def __init__(self, ns, name, spec):
        super(GnuplotFunction, self).__init__(name)
        self.__ns = ns
        self.__spec = spec

    defargs = property(lambda self: self.__spec.args)
    defbody = property(lambda self: self.__spec.body)
    arity = property(lambda self: len(self.defargs))
    defn = property(lambda self: '{}({}) = {}'.format(self.name,
                                                      ', '.join(self.defargs),
                                                      self.defbody))
    __defn_pattern = re.compile('\s*(?P<name>\S+)\s*\(\s*(?P<args>.+)\s*\)\s*=\s*(?P<body>.+)\s*')

    @property
    def gnuplot_id(self):
        return 'GPFUN_' + self.name

    def cast(self):
        return self.__spec

    def parse(self, s):
        m = self.__defn_pattern.match(s)
        if m:
            return GnuplotFunctionSpec(map(lambda e: e.strip(),
                                           m.group('args').split(',')),
                                       m.group('body'))
        else:
            raise ValueError('Bad function definition : \'{}\''.format(s))

    def __call__(self, *args):
        """Tells Gnuplot to evaluate this function

        :param args:
            :type: `iterable`
            Call arguments

        :returns:
            The evaluation of this function agains the given arguments

        """
        return self.__ns.eval(self, args)

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
        if len(args) < 1:
            raise ValueError('Cannot pack against 0 arguments')
        return self.name + '(' + ', '.join(args) + ')'

    def __getitem__(self, args):
        """A shorthand and syntactic sugar for pack

        .. see::
            `GnuplotFunction.pack`

        Example:
        f.pack('x', 'y', 'z') --> 'f(x, y, z)'

        """
        return self.pack(*args)


class GnuplotValueProxy(object):
    
    def __init__(self, name):
        self.__instances = {}
        self.__name__ = name

    def __definable(self, ns, value):
        # Cast to variable
        if isinstance(value, (int, float, str, unicode, bytes)):
            if isinstance(value, GnuplotDefinable):
                value = value.cast()
            return _GnuplotVariable(self.__name__, value)
        elif isinstance(value, GnuplotFunctionSpec):
            return GnuplotFunction(ns, self.__name__, value)
        else:
            raise ValueError('Can not cast \'{}\' to \'{}\'' \
                             .format(value, self.__class__.__name__))

    def existsFor(self, ns):
        return ns in self.__instances

    def __get__(self, ns, cls):
        if not ns in self.__instances:
            raise AttributeError('\'{}\' object has no attribute \'{}\'' \
                                 .format(cls.__name__, self.__name__))
        return self.__instances[ns]

    def __set__(self, ns, value):
        self.__instances[ns] = self.__definable(ns, value)

    def __delete__(self, ns):
        self.__instances.pop(ns)


class Namespace(type):

    def __init__(cls, name, bases, attrs, **kwargs):
        def __base():
            return bases[0] if bases else object
        def __setattr(self, name, value, *args, **kwargs):
            if hasattr(self, '__ns_init_done__'):
                if not name in self.__ns_protected__:
                    self.__define__(name, value, *args, **kwargs)
                    return
            __base().__setattr__(self, name, value)
        def __delattr(self, name, *args, **kwargs):
            if hasattr(self, '__ns_init_done__'):
                if not name in self.__ns_protected__:
                    self.__undefine__(name, *args, **kwargs)
                    return
            __base().__delattr__(self, name)
        type.__init__(cls, name, bases, attrs, **kwargs)
        cls.__ns_protected__ = \
            itertools.chain((e for e in getattr(cls, '__ns_protected__', ())),
                            (e for base in bases \
                             for e in getattr(base, '__ns_protected__', ())))
        cls.__setattr__ = __setattr
        cls.__delattr__ = __delattr

    def __call__(cls, *args, **kwargs):
        instance = type.__call__(cls, *args, **kwargs)
        instance.__ns_init_done__ = True
        return instance


class GnuplotNamespace(with_metaclass(Namespace, object)):
    """A namespace that manages access to Gnuplot variables and functions

    :param context:
        :type: `GnuplotContext`
        The enclosing Gnuplot context

    Example :
    
    >>> from .gnuplot import Gnuplot
    >>> with Gnuplot() as gp:
    ...     gp.max = 99                            # define 'max' variable
    ...     print(gp.max)                          # retrieve 'max' value
    ...     gp.f = gp.function(['x'], 'x + 1')     # define 'f(x)' function
    ...     print(gp.f.arity)
    ...     print(gp.f.gnuplot_id)
    ...     print(gp.f(1))                         # evaluate 'f(1)'
    ...     gp.max = 10.0                          # set 'max' value to 10
    ...     print(gp.max)                          # retrieve 'max' new value
    ...     print(gp.f(10))                        # evaluate 'f(10)'
    ...     print(gp.f['a', 'b'])
    ...     del gp.max                             # undefine 'max'
    ...     try:
    ...         gp.max
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
        super(GnuplotNamespace, self).__init__()
        self.__context = context
        self.__defined = set()
        self.define = self.__define__

    def __getProxy(self, name, default=VOID):
        cls = self.__class__
        proxy = cls.__dict__.get(name, default)
        if proxy is VOID:
            raise AttributeError('\'{}\' object has no attribute \'{}\'' \
                                 .format(cls, name))
        return proxy


    def __define__(self, name, value, timeout=-1):
        """Define a value in Gnuplot

        :param name:
            :type: `str`
            Name of the value to define
        :param value:
            :type: `mixin`
            The definition value

        """
        v = self.__getProxy(name, GnuplotValueProxy(name))
        v.__set__(self, value)
        self.__context.cmd(v.__get__(self, self.__class__).defn,
                           timeout=timeout)
        if not name in self.__class__.__dict__:
            setattr(self.__class__, name, v)
            self.__defined.add(name)
        return getattr(self, name)

    def sync(self, value, timeout=-1):
        expr = self.__context.cmd('printerr ' + value.gnuplot_id, timeout=timeout)
        proxy = self.__getProxy(value.name)
        proxy.__set__(self, type(value).parse(expr))

    def clear(self, timeout=-1):
        """Clear the namespace

        :param timeout:
            :type: `Number or None`
            Number of seconds to wait for a Gnuplot response, defaults to
            `GnuplotContext.defaultTimeout`

        """
        while self.__defined:
            self.__delattr__(self.__defined.pop(), timeout=timeout)

    def __undefine__(self, name, timeout=-1):
        value = getattr(self, name)
        self.undefine(value, timeout=timeout)
    
    def undefine(self, value, timeout=-1):
        """Undefine a value in Gnuplot

        The value is removed from Gnuplot and it's namespace

        :param value:
            :type: `GnuplotDefinable`
            The value to delete
        :param timeout:
            :type: `float or None`
            Number of seconds to wait for a Gnuplot response, defaults to
            `GnuplotContext.defaultTimeout`

        """
        self.__context.cmd('undefine ' + value.gnuplot_id, timeout=timeout)
        self.__getProxy(value.name).__delete__(self)
        self.__defined.discard(value.name)
    
    def eval(self, fun, args, timeout=-1):
        """Evaluate an expression inside Gnuplot

        :param fun:
            :type: `GnuplotFunction`
            Function to evaluate
        :param args:
            :type: `Iterable`
            Arguments to pass to the function

        :returns:
            fun(*args)

        """
        result = self.__context.cmd('printerr ' + fun.name + \
                                    '(' + ', '.join(map(str, args)) + ')',
                                    timeout=timeout)
        return _parseGnuplotValue(result)


    def __dir__(self):
        to_remove = (name for name in self.__defined \
                     if not self.__class__.__dict__[name].existsFor(self))
        attributes = dir(GnuplotNamespace) + list(self.__dict__.keys())
        for it in to_remove: attributes.remove(it)
        return attributes
