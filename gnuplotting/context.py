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


import os
import itertools

from .platform import print_function, unicode
from .figure import GnuplotFigure
from .variable import GnuplotNamespace, GnuplotFunction


class GnuplotContext(object):

    NO_WAIT = float()
    __FLUSH_INTERACTIVE = lambda self: ('' for c in os.linesep * 50)

    def __init__(self):
        super(GnuplotContext, self).__init__()
        self.__vars = GnuplotNamespace(self)

    vars = property(lambda self: self.__vars)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.terminate()
        return None

    def __ignoreKwarg(self, key, **kwargs):
        kwargs.pop(key, True)

    def send(self, lines, **kwargs):
        raise NotImplementedError

    def cmd(self, cmd, inline_data=(), **kwargs):
        """Send a command for evaluation to gnuplot

        This is purely syntactic sugar around `GnuplotContext.send`

        :param cmd:
            :type `str`:
            Command to send to gnuplot.
        :param inline_data:
            :type `iterable(str)`:
            An iterable of data string to send to gnuplot as inline data.
        :param kwargs:
            :type `mapping`:
            Optionnal arguments to pass to `GnuplotContext.send`

        :returns:
            The output if any given by gnuplot after evaluation of the
            command.

        :raises:
            `GnuplotError`
                If any error is reported by the gnuplot process.
            `GnuplotTimeoutError`
                If the command sent to gnuplot does not respond until the given
                `timeout` occurs.

        >>> from .gnuplot import Gnuplot
        >>> from .errors import GnuplotError
        >>> with Gnuplot() as gp:
        ...     gp.cmd('set xrange [0:10]; set yrange [-2:2]')
        ...     gp.cmd('plot tan(x)')
        ...     gp.cmd('plot sin(x)')
        ...     try:
        ...         gp.cmd('abcdef')
        ...     except GnuplotError as e:
        ...         assert e.cause == 'abcdef', "Bad error cause"
        ...         assert e.line == 0, "Bad error line"
        ...         assert e.msg == 'invalid command', "Bad error message"
        ...
        ...     gp.cmd('f(x) = 1 + 2*x + 3*x**2')
        ...     gp.cmd('plot f(x)')
        ...     gp.cmd("plot '-' using 1:2 with linespoint",
        ...            inline_data=['1 2', '3 4', '5 6', 'e'])
        ...     # NO_WAIT is used to avoid hanging
        ...     gp.cmd('quit', timeout=gp.NO_WAIT)
        ...
        ...

        """
        # Argument checking
        if not isinstance(cmd, (str, unicode)):
            raise TypeError("'cmd' argument must be a string, given '{}'" \
                            .format(cmd))
        if not hasattr(inline_data, '__iter__'):
            raise TypeError("'inline_data' argument must be an iterable")
        return self.send(itertools.chain((cmd,), inline_data), **kwargs)

    def interactiveCmd(self, cmd, *args, **kwargs):
        """Run a Gnuplot interactive command

        :param cmd:
            :type: `str`
            The name of the gnuplot command
        :param args:
            :type: `iterable of str`
            The command parameters
        :param kwargs:
            :type: `dict-mapping`
            Additionnal arguments to pass to `GnuplotContext.cmd`

        :returns:
            The result of the command

        :raises:
            `GnuplotError`
                If gnuplot reports an error
            `GnuplotTimeoutError`
                If a timeout occured while processing the command

        ..note::
            `inline_data` in kwargs is always ignored

        Example:

        >>> from .gnuplot import Gnuplot
        >>> with Gnuplot() as gp: # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        ...     # An example with a timeout
        ...     print(gp.interactiveCmd('help', 'fit', timeout=0.5))
        ...
        The `fit` ...

        """
        self.__ignoreKwarg('inline_data', **kwargs)
        return self.cmd(cmd + ' ' + ' '.join(map(str, args)),
                        inline_data=self.__FLUSH_INTERACTIVE(), **kwargs)

    def supportsTimeout(self):
        raise NotImplementedError

    def terminate(self):
        """Terminate the current gnuplot context.

        This method releases any underlying resource held by the gnuplot context

        ..note::
            When used in a context manager (ie: in a `with` statement),
            `terminate` is implicitely called before exiting the context manager

        Example:

        >>> from .gnuplot import Gnuplot
        >>> gp = Gnuplot()
        >>> gp.terminate()
        >>> gp.terminate() # terminate may be used multiple times

        >>> with Gnuplot() as gp:
        ...     # terminate is called implicitely in context managers
        ...     pass
        ...

        >>> with Gnuplot() as gp: # terminate may be used multiple times
        ...     gp.terminate()
        ...     gp.terminate()
        ...

        """
        try: self.__vars.clear()
        except ValueError: pass

    def quit(self):
        """ Send the `quit` command to gnuplot

        ..note::
            This method *DOES NOT* release resources held by the gnuplot
            context.
            You *MUST* use a context manager or the `terminate` method in order
            to properly release them.

        Example:

        >>> from .gnuplot import Gnuplot
        >>> with Gnuplot() as gp:
        ...     gp.quit()


        Or:

        >>> gp = Gnuplot()
        >>> gp.quit()
        >>> gp.terminate()

        """
        self.cmd('quit', timeout=self.NO_WAIT)

    def help(self, *topics, **kwargs):
        """Return the gnuplot internal help

        :param topics:
            :type: `iterable of str`

        :returns:
            A string describing the gnuplot's internal help or `None` if backend
            is a file-like object

        Example:

        >>> from .gnuplot import Gnuplot
        >>> with Gnuplot() as gp: # doctest: +ELLIPSIS, +NORMALIZE_WHITESPACE
        ...     # An example with a timeout
        ...     print(gp.help('bind', timeout=0.5))
        ...
        Syntax: ...

        """
        return self.interactiveCmd('help', *topics, **kwargs) 

    def show(self, *topics, **kwargs):
        return self.interactiveCmd('show', *topics, **kwargs)


    def shell(self, *shell_cmds, **kwargs):
        """Use the gnuplot shell command

        :param shell_cmds:
            :type: `iterable(str)`
            A collection of shell commands to execute
        :param kwargs:
            :type: dict
            Optional parameters used by ``Gnuplot.cmd``

        :returns:
            The concatened result of each executed command as a string or `None`
            if backend is a file-like object 

        ..note::
            Because there is no portable way to quit the shell command, you
            *MUST* always add a quit-like command at the end of `shell_cmds`,
            or use `timeout=gp.NO_WAIT` in order to skip output checking.

        ..note::
            `inline_data` in kwargs is always ignored


        Example:

        >>> from .gnuplot import Gnuplot
        >>> with Gnuplot() as gp: # doctest: +SKIP
        ...     print(gp.shell('echo "hello"', \
                               'echo "world"', \
                               'exit'))
        hello
        world

        >>> with Gnuplot() as gp: # doctest: +SKIP
        ...     # we can't retrieve the output here, since we use NO_WAIT
        ...     gp.shell('echo "hello"', timeout=gp.NO_WAIT)
        ...     # To exit the shell command we must send exit as a regular
        ...     # command and tweak with the sync parameter
        ...     gp.cmd('exit', sync=(gp.OSECHO, gp.PRINTERR))

        """
        self.__ignoreKwarg('inline_data', **kwargs)
        res = self.cmd('shell', inline_data=shell_cmds, **kwargs)
        if res:
            # Removes the trailing linesep resulting of empty commands
            res = res.rstrip(os.linesep)
        return res

    def function(self, args, body):
        return GnuplotFunction(self.vars, args, body)
    
    def Figure(self, id=None, title=None,
               term=None, options=None, output=None):
        """Create a new Gnuplot figure

        :param id:
            :type: `int`
            Id of the figure, it mirrors the gnuplot window id, defaults to a
            unique generated id
        :param title:
            :type: `str`
            Title of the figure, defaults to no title
        :param term:
            :type: `str`
            Gnuplot terminal to use, defaults to the current terminal
        :param options:
            :type: `tuple of str`
            Gnuplot termoptions to use for the figure, defaults to no options
        :param output:
            :type: `str`
            Gnuplot output to use, defaults to the default terminal output

        >>> from .gnuplot import Gnuplot
        >>> with Gnuplot() as gp:
        ...     fig1 = gp.Figure(title='My awesome figure')#, term='wxt')
        ...     fig1.plot('sin(x)', _with='linespoints')
        ...     fig1.plot('tan(x)', sampling_range='[-pi:pi]', title='tan(x)')
        ...     fig1.submit(timeout=5)
        ...     fig2 = gp.Figure(title='Another awesome figure')#, term='wxt')
        ...     gp.vars.f = gp.function(['u', 'v'], '(cos(u), sin(v))')
        ...     fig2.splot(gp.vars.f['x', 'y'], _with='pm3d')
        ...     fig2.submit(timeout=5, wait=True)
        ...

        """
        return GnuplotFigure(self, id=id, title=title, term=term,
                             options=options, output=output)
