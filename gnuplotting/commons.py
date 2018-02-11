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


from .utils import VOID
from .platform import map

class UserValue(object):

    def __init__(self, name, value, allowed_types):
        if not isinstance(name, str):
            raise TypeError("'name' argument must be a string")
        self.__name = name
        self.__allowed_types = allowed_types
        self.__checkType(value)
        self.__value = value

    def __checkType(self, value):
        if not isinstance(value, self.__allowed_types):
            raise TypeError("'{}' value must be of type {}" \
                            .format(self.__name,
                                    'or '.join(map(lambda it: \
                                                       '`' + it.__name__ + '`',
                                                   self.__allowed_types))))

    def name(self):
        return self.__name

    def __call__(self, value=VOID):
        if value is VOID:
            return self.__value
        else:
            self.__checkType(value)
            self.__value = value
    

def userVal(self, name, value, allowed_types):
    uv = UserValue(name, value, allowed_types)
    setattr(self, name, uv)
