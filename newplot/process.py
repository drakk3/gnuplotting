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


import os
import time
import logging
import itertools
import subprocess

from .utils import CallableGenerator, NoOp, isnumber
from .platform import map, DEFAULT_GNUPLOT_CMD, print_function
from .context import GnuplotContext
from .multithreading import (threading, queue, Event, Future,
                             FutureTimeoutError, LockedGenerator)
from .errors import GnuplotError, GnuplotTimeoutError, parseError


class _GnuplotOutputReader(threading.Thread):
    """A thread that reads the gnuplot output

    It waits for requests to read the output and parse it for errors
    It is not intended to be used by end users

    """
    def __init__(self, gnuplot_stdout, no_wait, id = 1):
        threading.Thread.__init__(self,
                                  target=self.__run,
                                  name='GnuplotOutputReader-%d' % id)
        self.setDaemon(True)
        self.__input = gnuplot_stdout
        self.__lock = threading.RLock()
        self.__doing = set()
        self.__requests = queue.Queue()
        self.__stop = Event()
        self.__NO_WAIT = no_wait

    def stop(self):
        if not self.__stop():
            # Set the stop flag
            self.__stop(True)
            # Purge the request queue
            while not self.__requests.empty():
                todo, beginToken, doneToken = self.__requests.get()
                todo.abort()
            # Put None in the queue in case it is blocked in get()
            self.__requests.put(None)
            # Purge the doing set
            with self.__lock:
                while len(self.__doing) > 0:
                    self.__doing.pop().abort()

    def requestOutput(self, cause, beginToken, doneToken, timeout = None):
        if timeout == self.__NO_WAIT:
            return ('', '')
        future = Future(self.__consumeUntilDone)
        self.__requests.put((future, beginToken, doneToken))
        try:
            return future.waitDone(timeout)
        except FutureTimeoutError:
            future.abort()
        raise GnuplotTimeoutError({'cause': cause, 'timeout': timeout})

    def __consumeUntilDone(self, abort, beginToken, doneToken):
        def addToBuffer(buf, line):
            buf += line
        # Consume the output until the stop token is reached or cancellation
        buff = ''
        beginToken = beginToken + os.linesep
        doneToken = doneToken + os.linesep
        while not (buff.endswith(doneToken) or abort()):
            c = self.__input.read(1)
            if c:
                buff += c.decode(errors='replace')
        start = buff.find(beginToken)
        if start > -1:
            unsync = ''
            if start > 0:
                unsync = buff[:start-1]
            return unsync, buff[start + len(beginToken):-(len(doneToken) + 1)]
        else:
            return '', buff[:-(len(doneToken) + 1)]

    def __run(self):
        while not self.__stop():
            # Take a read request
            request = self.__requests.get()
            # Extract it
            if request is not None:
                todo, beginToken, doneToken = request
                # Tag it as doing
                with self.__lock:
                    self.__doing.add(todo)
                # Do it
                todo(beginToken, doneToken)
                # When done untag it
                self.__requests.task_done()
                with self.__lock:
                    try:
                        self.__doing.remove(todo)
                    except KeyError:
                        # The stop method may have already untag
                        # this task: the error is ignored
                        pass


class GnuplotProcess(GnuplotContext):
    """A class that provides a 2-way communication API with a gnuplot process.

    Synchronization with the backend process is made by forcing gnuplot to
    enclose each command output with a start and end token using a print
    command. Be aware that this behaviour could mess up the gnuplot history.

    :attr NO_WAIT:
        A value that turns off output checking
    :attr PRINTERR:
        A value that tells gnuplot to use the `printerr` command for
        synchronization
    :attr OSECHO:
        A value that tells gnuplot to use the os echo command for
        synchronization. Only usefull in conjunction with the `shell` command.
        Experimental on non UNIX systems
    :attr id:
        A unique id associated with the current instance. Usefull to track the
        logs when using multiple instances at the same time
    :attr version:
        Version of the gnuplot backend

    :param cmd:
        :type: str
        A path-like string pointing to the gnuplot backend executable
    :param args:
        :type: iterable
        An iterable of parameters to pass to the gnuplot backend
    :param log:
        :type: bool
        A boolean value that turns logging on (`True`) or off (`False`)
        Defaults to `False`
    :param defaultTimeout:
        :type: `None or float`
        A default timeout used while sending commands to gnuplot. `None` means
        wait forever for a response.

    """
    PRINTERR = "printerr '%s'"
    OSECHO = "echo '%s'"

    __BEGIN_TOKEN_FORMAT = '<newplot-{id}-{cmd_id}>'
    __DONE_TOKEN_FORMAT = '<newplot-{id}-{cmd_id}-done>'
    __EVENT_TOKEN = '<newplot-{id}-{event}-{evt_id}>'

    __uniqueId = CallableGenerator(LockedGenerator(itertools.count(1, 1)))

    def __init__(self, cmd=DEFAULT_GNUPLOT_CMD,
                       args=(),
                       log=False,
                       defaultTimeout=None):
        super(GnuplotProcess, self).__init__()
        if not isinstance(cmd, str):
            raise TypeError("'cmd' argument must be a path-like string "
                            "pointing to the gnuplot executable")
        if not hasattr(args, '__iter__'):
            raise TypeError("'args' argument must be an iterable")
        if not isinstance(log, bool):
            raise TypeError("'log' argument must be a boolean value")
        if not (defaultTimeout is None or \
                 (isnumber(defaultTimeout) and defaultTimeout >= 0)):
            raise TypeError("'defaultTimeout' argument must be None or a >= 0 "
                            "number")
        self.id = self.__uniqueId()
        self.__backend = subprocess.Popen([cmd] + list(map(str, args)),
                                          stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT,
                                          bufsize=0)
        self.__stdin = self.__backend.stdin
        self.__stdout = self.__backend.stdout
        self.__genCmdId = \
            CallableGenerator(LockedGenerator(itertools.count(0, 1)))
        self.__logger = self.__initLogger(log)
        self.__defaultTimeout = defaultTimeout
        self.__reader = _GnuplotOutputReader(self.__stdout,
                                             self.NO_WAIT, self.id)
        self.__reader.start()
        self.version = lambda: self.cmd(self.__print('GPVAL_VERSION'))

    @property
    def isinteractive(self):
        return True

    def stop(self):
        """Stop the gnuplot process

        >>> with GnuplotProcess() as gp:
        ...     gp.stop()
        ...

        """
        # Close the streams => send EOF to gnuplot
        self.__stdin.close()
        self.__stdout.close()
        # Requests reader for stopping
        self.__reader.stop()
        if self.__backend.poll() is None: 
            # Wait 1 second for gnuplot to stop
            time.sleep(1)
            self.__backend.terminate()
            if self.__backend.poll() is None:
                # if gnuplot is still alive, wait 4 more seconds, then kill it
                time.sleep(4)
                if self.__backend.poll() is None:
                    self.__backend.kill()
        self.__reader.join()


    def terminate(self):
        super(GnuplotProcess, self).terminate()
        self.stop()
        

    def __print(self, to_print):
        return 'printerr %s' % to_print

    def __initLogger(self, log):
        if log:
            return logging.getLogger('%s-%d' % \
                                     (self.__class__.__module__ + \
                                      self.__class__.__name__, self.id))
        else:
            return NoOp()

    def __sendLine(self, line):
        self.__logger.info('Sending `%s`' % line)
        self.__stdin.write((line + os.linesep).encode())

    def __getTimeout(self, timeout):
        if isnumber(timeout) and timeout < 0:
            timeout = self.__defaultTimeout
        return timeout

    __authorized_sync = frozenset((PRINTERR, PRINTERR))

    def send(self, lines, timeout=-1, sync=(PRINTERR, PRINTERR)):
        """Send lines for evaluation to gnuplot

        Lines are sent to gnuplot on stdin and if `timeout` is not 'NO_WAIT`,
        the output is checked after evaluation and returned. If errors are
        reported by gnuplot, they're raised as exceptions, . If `timeout` is
        `NO_WAIT`, the output is not checked and `None``is returned.

        .. note::
            When `timeout` is not `NO_WAIT`, lines sent to gnuplot are
            enclosed with 2 synchronization token printing comands.
            This can pollute the gnuplot's internal history.

        :param lines:
            :type `iterable of str`:
            Lines to send to gnuplot.
        :param timeout:
            :type `float or None`:
            Wait at most timeout seconds for a response.
            Negative value means defaultTimeout, None means forever,
            `NO_WAIT` means do not wait for gnuplot process response. Defaults
            to `defaultTimeout (-1)`.
        :param sync:
            :type `2-tuple`:
            Specify wich method is used to output synchronization
            tokens. The first component is for the begin-token, the second for
            the done-token. Valid values for each component are `PRINTERR`or
            `OSECHO`.

        :returns:
            The output if any given by gnuplot after evaluation of the lines.

        :raises:
            `GnuplotError`
                If any error is reported by the gnuplot process.
            `GnuplotTimeoutError`
                If Gnuplot does not respond until the given
                `timeout` occurs.

        >>> with GnuplotProcess() as gp:
        ...     gp.send(('set xrange [0:10]; set yrange [-2:2]',))
        ...     gp.send(('plot tan(x)',))
        ...     gp.send(('plot sin(x)',))
        ...     try:
        ...         gp.send(('abcdef',))
        ...     except GnuplotError as e:
        ...         assert e.cause == 'abcdef', "Bad error cause"
        ...         assert e.line == 0, "Bad error line"
        ...         assert e.msg == 'invalid command', "Bad error message"
        ...
        ...     gp.send(('f(x) = 1 + 2*x + 3*x**2',))
        ...     gp.send(('plot f(x)',))
        ...     gp.send(("plot '-' using 1:2 with linespoint",
        ...                 '1 2',
        ...                 '3 4',
        ...                 '5 6',
        ...                 'e'))
        ...     # NO_WAIT is used to avoid hanging
        ...     gp.send(('quit',), timeout=gp.NO_WAIT)
        ...
        ...

        """
        if not (hasattr(sync, '__iter__') and len(sync) == 2):
            raise TypeError("'sync' argument must be a 2-tuple")
        for _sync in sync:
            if not _sync in self.__authorized_sync:
                raise TypeError("'sync' argument must be PRINTERR or OSECHO")
        timeout = self.__getTimeout(timeout)
        timeout_is_no_wait = timeout == self.NO_WAIT
        # Generate uniques begin and done tokens for this command
        cmd_id = self.__genCmdId()
        beginToken, doneToken = (form.format(id=self.id, cmd_id=cmd_id) \
                                 for form in (self.__BEGIN_TOKEN_FORMAT,
                                              self.__DONE_TOKEN_FORMAT))
        printBeginToken, printDoneToken = (form % token for (form, token) in \
                                           zip(sync, (beginToken, doneToken)))
        # Send the command, tell gnuplot to print the begin token before,
        # and the done token after:
        if not timeout_is_no_wait: self.__sendLine(printBeginToken)
        for line in lines: self.__sendLine(line)
        if not timeout_is_no_wait: self.__sendLine(printDoneToken)
        self.__stdin.flush()
        # Ask for parsing the output during at most timeout seconds
        unsync_result, result = \
            self.__reader.requestOutput('Sending ' + beginToken,
                                        beginToken,
                                        doneToken, timeout)
        if unsync_result:
            self.__logger.warning('unsync output: %s' % unsync_result)
        if result:
            self.__logger.info('sync output: %s' % result)
        # Parse for errors
        error = parseError(result)
        if error:
            raise GnuplotError(error)
        # return the result
        return result or None

    def wait(self, evts=(), timeout=-1):
        """Wait for gnuplot events to happen

        :param evts:
            :type: `iterable` of `2-tuple`
            Each tuple describe an event to wait for and must conform to the
            following shape : ('<term_type>[_<window_id>], '<event_name>').

            Example :
                ('qt': 'Close')
                    Represents the Close event for the current window of the
                    qt terminal
                ('wxt_1': 'ctrl-a')
                    Represents the "ctrl-a" keypress event inside the '1'
                    window of the wxt terminal

            Available events are those described by the 'help bind' gnuplot
            command.
        :param timeout:
            :type: `float or None`
            The current thread will wait at most `timeout` seconds *FOR EACH*
            event to occur. If given without `evts` the current thread will
            sleep for `timeout` seconds. Defaults to
            `GnuplotProcess.defaultTimeout`.

        :raises:
            `GnuplotError`
                if an event is not supported
            `GnuplotTimeoutError`
                if a `timeout` occurs during waiting for an event
            
        .. warnings::
            1. This command only works with mouse-capable terminals as it uses
               the `bind` gnuplot command.
            2. The provided events are waited in order. For 2 provided events
               (e1, e2), if `e2` occurs before `e1`, then none of the 2 events
               will be catched (unless `e1` == `e2`).
            3. If timeout is not provided and defaults to `None`
               (ie wait forever), make sure that the given events points to
               existing windows, otherwise the call will never return.
            4. Given 2 and 3, it's a good practice to always provide a
               `timeout` > 0 or rely on a > 0 default timeout.

            
        >>> with GnuplotProcess(log=True) as gp:
        ...     gp.cmd('set term qt 0')
        ...     gp.cmd('plot sin(x)')
        ...     gp.cmd('set term qt 1')
        ...     gp.cmd('plot cos(x)')
        ...     # Setting up the closer thread :
        ...     # NO_WAIT is used here because otherwise it will end to a
        ...     # deadlock : the worker thread is already busy, listening for
        ...     # a 'Close' token
        ...     wait = 0.5
        ...     t = threading.Thread(target=lambda: time.sleep(wait) or \
                                     gp.cmd('set term qt 0 close',
        ...                                 timeout=gp.NO_WAIT) or \
                                     time.sleep(0.05) or \
                                     gp.cmd('set term qt 1 close',
        ...                                 timeout=gp.NO_WAIT))
        ...     t.setDaemon(True)
        ...     tip = time.time()
        ...     t.start()
        ...     gp.wait([('qt_0', 'Close'),
        ...             ('qt_1', 'Close')], timeout=5)
        ...     gp.wait(timeout=wait)
        ...     top = time.time()
        ...     t.join()
        ...     check = wait * 3 + 0.05
        ...     assert top - tip < check, \
                       "Failed to wait for the plot windows to close " \
                       "automatically in %s seconds" % check

        """
        timeout = self.__getTimeout(timeout)
        if evts:
            # Saves the current terminal
            self.cmd('set term push', timeout=self.NO_WAIT)
            try:
                for (term, evt) in evts:
                    term_spec = term.split('_')
                    term_name = term_spec[0]
                    term_id = int(term_spec[1]) if len(term_spec) > 1 else '' 
                    bind_evt = 'bind ' + evt
                    evt_id = self.__genCmdId()
                    evt_token = self.__EVENT_TOKEN.format(id=self.id, event=evt,
                                                          evt_id=evt_id)
                    bind_cmd = bind_evt + ' {printToken}' \
                               .format(evt=evt,
                                       printToken=self.__print('"%s"' % \
                                                               evt_token))
                
                    # Switching to the target terminal window
                    self.cmd('set term {} {}'.format(term_name, term_id),
                             timeout=self.NO_WAIT)
                    # Force it to raise with 'refresh', it's dirty but 'raise'
                    # is not reliable
                    self.cmd('refresh', timeout=self.NO_WAIT)
                    # Bind the event
                    self.cmd(bind_cmd, timeout=self.NO_WAIT)
                    try:
                        # Wait for the event token
                        self.__reader.requestOutput('Waiting for {}({}) event' \
                                                    .format(evt, evt_id),
                                                    '', evt_token, timeout)
                    finally:
                        # Unbind evt
                        self.cmd(bind_evt + ' ""', timeout=self.NO_WAIT)
            finally:
                # Restore the original terminal
                self.cmd('set term pop', timeout=self.NO_WAIT)
        elif isnumber(timeout) and timeout > 0:
            time.sleep(timeout)
        else:
            raise TypeError("'timeout' argument must be > 0 if provided alone")
