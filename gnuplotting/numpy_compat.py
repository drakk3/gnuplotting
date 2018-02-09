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

from .platform import print_function

try:

    from numpy import ufunc, zeros, asarray, newaxis, savetxt, shape
    arraytype = lambda a: a.dtype.char
    vadd = lambda a, b: a + b

except ImportError:

    import copy
    import warnings
    from itertools import product

    from .platform import reduce, map
    from .utils import iterable

    warnings.warn("Numpy isn't available on this environment, falls back to raw"
                  " Python mode. Note that this can be significantly slower",
                  stacklevel=2)
    
    ufunc = type(None)
    newaxis = None
    vadd = lambda a, b: list(map(lambda aa, bb: aa + bb, a, b))
    
    def zeros(shape, dtype=float):
        """An emulation of numpy `zeros` function

        Return a new array of given shape and type, filled with zeros.

        :param shape:
            :type: int or seq(int)
            Shape of the new array, e.g., ``(2, 3)`` or ``2``.
        :param dtype:
            :type: data-type, optional
            The desired data-type for the array, e.g., `int`. Default is `float`

        :returns:
            A new array of given shape and type, filled with zeros.

        >>> zeros(5, int)
        [0, 0, 0, 0, 0]

        >>> zeros((1, 2), int)
        [[0, 0]]

        >>> zeros((2, 1, 3), int)
        [[[0, 0, 0]], [[0, 0, 0]]]

        >>> zeros((2, 1, 3), float)
        [[[0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0]]]

        """
        if isinstance(shape, int):
            shape = (shape,)
        res = dtype()
        for dim in reversed(shape):
            res = [copy.deepcopy(res) for _ in range(dim)]
        return res

    def arraytype(a):
        """Returns the type of an homogeneous array (like numpy `.dtype`)

        :param a:
            :type: array-like

        :returns:
            The class type of the first element of `a`

        >>> arraytype([0, 1, 3]) is int
        True

        >>> arraytype(((1, 2),)) is int
        True

        >>> arraytype([1.0, 1, 3, 'A']) is float
        True

        >>> arraytype(((('A', 3, 5)), ((2)), ((((1, 4, 4), 5))))) is str
        True

        """
        if iterable(a):
            for aa in a:
                if not aa is a:
                    return arraytype(aa)
                break
        return type(a)

    def asarray(a, dtype=None):
        """An emulation of numpy `asarray` function

        Convert the input to an array.

        :param a:
            :type: array-like
            Input data, in any form that can be converted to an array.  This
            includes lists, lists of tuples, tuples, tuples of tuples, tuples
            of lists and ndarrays.dtype :
        :param dtype:
            :type: data-type, optional
            By default, the data-type is inferred from the input data.

        :returns:
            The input converted to an fake-array (a list of lists) of the given
            dtype

        >>> asarray([])
        []

        >>> asarray(1, float)
        [1.0]

        >>> asarray(((0, 1, 3), (1, 2)), float)
        [[0.0, 1.0, 3.0], [1.0, 2.0]]

        >>> asarray((1, 2))
        [1, 2]

        >>> asarray(((1, 2),))
        [[1, 2]]

        >>> asarray('myarray')
        ['m', 'y', 'a', 'r', 'r', 'a', 'y']

        >>> asarray(((1, 2), ((3, 4), 5), (6, (8, (9,), 10, 11), 12)), float)
        [[1.0, 2.0], [[3.0, 4.0], 5.0], [6.0, [8.0, [9.0], 10.0, 11.0], 12.0]]
        
        """
        def _asarray(a, first, dtype):
            if dtype is None:
                dtype = arraytype(a)
            if iterable(a):
                return [_asarray(aa, False, dtype) \
                        if not aa is a and not isinstance(aa, dtype) \
                        else dtype(aa) for aa in a]
            return [dtype(a)] if first else dtype(a)
        return _asarray(a, True, dtype)

    def shape(a):
        """An emulation of numpy `shape` function

        Return the shape of an array.

        :param a:
            :type: array-like
            Input array

        :returns:
            A tuple of ints, the elements of the shape tuple give the lengths of
            the corresponding array dimensions.

        >>> shape(zeros((1,)))
        (1,)

        >>> shape(zeros((2, 1, 3)))
        (2, 1, 3)

        >>> shape(zeros((2, 4, 1, 5, 3), float))
        (2, 4, 1, 5, 3)

        >>> shape('abcd')
        (4,)

        >>> shape(())
        ()

        """
        if iterable(a):
            n = 0
            aaa = None
            for i, aa in enumerate(a):
                if aa is not a:
                    if i == 0:
                        aaa = aa
                    n += 1
            if n > 0:
                return (n,) + (shape(aaa) if aaa else ())
        return ()

    def transpose(a, axes=None):
        """An emulation of numpy `transpose` function

        Permute the dimensions of an array.

        :param a:
            :type: array-like
            Input array
        :param axes:
            :type: list of ints, optional
            By default, reverse the dimensions, otherwise permute the axes
            accordingly to the values given.

        :returns:
            A *NEW ARRAY* representing `a` with its axes permuted.

        >>> x = [[0, 1], [2, 3]]
        >>> transpose(x)
        [[0, 2], [1, 3]]

        >>> x = zeros((1, 2, 3))
        >>> shape(transpose(x))
        (3, 2, 1)

        >>> shape(transpose(x, (1, 0, 2)))
        (2, 1, 3)

        >>> transpose('abcd')
        ['a', 'b', 'c', 'd']

        >>> transpose((1,))
        [1]

        >>> transpose(())
        []

        >>> transpose([[3, 6, 9]])
        [[3], [6], [9]]

        >>> transpose([[[0, 1], [2, 3]], [[4, 5], [6, 7]]], (2, 1, 0))
        [[[0, 4], [2, 6]], [[1, 5], [3, 7]]]

        """
        if a:
            sh = shape(a)
            if axes is None:
                axes = range(len(sh)-1, -1, -1)
            tr = zeros(tuple((sh[i] for i in axes)), arraytype(a))
            for coords in product(*(range(i) for i in sh)):
                # print('coords:', coords)
                newcoords = tuple((coords[i] for i in axes))
                # print('newcoords:', newcoords)
                v = reduce(lambda acc, c: acc[c], coords, a)
                # print('v:', v)
                trv = reduce(lambda acc, nc: acc[nc], newcoords[:-1], tr)
                # print('trv:', trv)
                trv[newcoords[-1]] = v
                # print('tr:', tr)
            return tr
        return list(a)

    def savetxt(fname, X, fmt='%.18e', delimiter=' ', newline='\n', footer='',
                comments='# ', encoding=None):
        mode = 'wb' if encoding else 'w'
        encode = lambda s: s.encode(encoding) if encoding \
                 else lambda s: s
        with open(fname, mode, encoding=encoding, newline=newline) as f:
            map(lambda l:
                    f.write(encode(delimiter.join(map(str, l)) + newline)), X)
    
