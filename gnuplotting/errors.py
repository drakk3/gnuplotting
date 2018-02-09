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


import re

from .multithreading import TimeoutError


ERROR_PATTERNS = [
    re.compile(
        '(?:gnuplot>\s+(?P<cmd>[^\n]+)\s)?'
            '(?:\s+\^\n)?'
            '\s+line\s+(?P<line>[0-9]+):\s+(?P<msg>[^\n]+)\s+$', 
            re.M + re.S)
]


def parseError(output):
    for error_pattern in ERROR_PATTERNS:
        m = re.search(error_pattern, output)
        if m:
            fields = ['cmd', 'line', 'msg']
            return dict(zip(fields, (m.group(field) for field in fields)))
    return None

class GnuplotTimeoutError(TimeoutError):

    def __init__(self, error):
        self.cause = error['cause']
        self.timeout = error['timeout']

    def __str__(self):
        s = 'Gnuplot process did not respond in the given %f seconds, ' + \
            'WARNING: gnuplot may have crashed or been left in a weird state' +\
            '\n\tCause: %s'
        return s % (self.timeout, self.cause)


class GnuplotError(Exception):

    def __init__(self, error):
        self.cause = error['cmd'] if 'cmd' in error else None
        self.line = int(error['line']) if 'line' in error else None
        self.msg = error['msg']

    def __str__(self):
        s = self.msg
        if self.line is not None:
            s += ', line %d' % self.line
        if self.cause is not None:
            s += '\n\tGiven: %s' % self.cause
        return s
