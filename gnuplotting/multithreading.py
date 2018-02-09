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


from numbers import Number

from .platform import IS_PYTHON2
if IS_PYTHON2:
    import Queue as queue
    class TimeoutError(OSError):
        pass
else:
    import queue
    TimeoutError = TimeoutError

try:
    import threading
except ImportError:
    import dummy_threading as threading

class Event(object):
    """Events used in a multi-threading context

    They provides a convenient wrapper around `threading.Event`

    """
    def __init__(self):
        self.__backend = threading.Event()

    def __call__(self, value = None):
        """Retrieve or set the event value

        :param value:
            :type: `bool or None`
            Boolean value to set, None means only return the internal value
            (defaults to None)

        :returns:
            The event internal value

        >>> e = Event()
        >>> e()
        False
        >>> e(None)
        False
        >>> e(True)
        True
        >>> e(False)
        False
        >>> e(value = None)
        False
        >>> e(value = True)
        True
        >>> e(value = False)
        False

        """
        if value is True:
            self.__backend.set()
        elif value is False:
            self.__backend.clear()
        return self.__backend.is_set()

    def wait(self, timeout = None):
        """Waits at most timeout seconds for the event to be True

        :param timeout:
            :type `bool or None`
            Timeout value (None means infinity)

        >>> e = Event()
        >>> e.wait(1)
        False
        >>> e(True)
        True
        >>> e.wait()
        True

        """
        if not (timeout is None or \
                (isinstance(timeout, Number) and timeout >= 0)):
            raise TypeError("'timeout' argument must be None or a >= 0 number")
        return self.__backend.wait(timeout)


class FutureStateError(Exception):
    """An error raised if a future is called more than once."""
    pass


class FutureTimeoutError(Exception):
    """An error raised if waiting for a future result ends with a timeout."""
    pass


class Future(object):
    """A future object that can be waited for completion and eventually 
    cancelled.

    :param task:
        :type: `callable`
        A callable receiving at least one argument : the abort event. The event
        is set to True when the user requests the future to be cancelled. It is
        the responsability of this callable to take the user request into
        account.

    """
    def __init__(self, task):
        if not callable(task):
            raise TypeError("'task' argument must be a callable")
        self.__task = task
        self.__abort = Event()
        self.__done = Event()
        self.__lock = threading.RLock()
        self.__result = None

    def __call__(self, *args, **kwargs):
        """Run the future

        >>> @Future
        ... def task(abort):
        ...     return True
        >>> task()
        >>> task()
        Traceback (most recent call last):
            ...
        gnuplotting.multithreading.FutureStateError: This future can only be called once

        """
        self.__call(*args, **kwargs)

    def __call(self, *args, **kwargs):
        with self.__lock:
            self.__call = self.__cantCallTwice
        self.__result = self.__task(self.__abort, *args, **kwargs)
        self.__done(True)

    def __cantCallTwice(self, *args, **kwargs):
        raise FutureStateError('This future can only be called once')        

    def abort(self):
        """Requests the future for cancellation

        >>> import time
        >>> @Future
        ... def task(abort):
        ...     while not abort(): 
        ...         print('hello')
        ...         time.sleep(0.1)
        ...
        >>> t = threading.Thread(target = task)
        >>> t.start()
        hello
        >>> task.abort()
        >>> t.join()

        """
        self.__abort(True)

    def waitDone(self, timeout = None):
        """Wait for the future result

        :param timeout:
            :type `float or None`
            If not None the caller will wait at most timeout for the result. If
            the timeout is reached before a result is available, a
            `FutureTimeoutError` is raised, otherwise the result is returned.
            If None the caller will wait indefinitely for the result to be
            available.

        :returns:
            The result if it is available before a timeout occurs, None 
            otherwise.

        :raises:
            `FutureTimeoutError`, if a timeout occurs.

        >>> import time
        >>> @Future
        ... def task(abort):
        ...     while not abort(): 
        ...         print('hello')
        ...         time.sleep(0.3)
        ...
        >>> t = threading.Thread(target = task)
        >>> try:
        ...     t.start()
        ...     task.waitDone(0.5)
        ... except FutureTimeoutError as e:
        ...     print(e)
        ...     task.abort()
        ...
        hello
        hello
        Timed out after 0.500000 seconds
        >>> t.join()

        """
        if self.__done.wait(timeout):
            return self.__result
        else:
            raise FutureTimeoutError('Timed out after %f seconds' % timeout)
