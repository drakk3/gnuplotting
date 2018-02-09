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


from .platform import IS_PYTHON2


VOID = type('VOID', (object,), {})()

def isnumber(obj):
    return isinstance(obj, (int, float))

def isfloat(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def iterable(obj):
    """Check if an object is iterable

    :param obj:
        :type: `object`
        The object to check

    :returns:
        ``True`` if `obj` is an iterable, ``False`` otherwise

    """
    return hasattr(obj, '__iter__') or hasattr(obj, '__getitem__')

# Generator utility functions
def CallableGenerator(gen):
    """Turn a generator into a callable

    :param gen:
        :type: `genexpr`
        The generator to convert

    :returns:
        The `next` method of the given generator

    """
    return gen.next if IS_PYTHON2 else gen.__next__

class NoOp(object):

    def __getattr__(self, name, default=None):
        return self.noOp

    def noOp(self, *args, **kwargs):
        pass
