# -*- encoding: utf-8 -*-
import logging

__version__ = '0.0.8'

from .app import Worker
from .task import (
    stop_none, stop_after_attempt, stop_after_delay,
    wait_fixed, wait_incremental, wait_exponential
)

try:
    # not available in python 2.6
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):

        def emit(self, record):
            pass

# Add NullHandler to prevent logging warnings
logging.getLogger(__name__).addHandler(NullHandler())


class TaskNotRegistered(Exception):
    '''It can be raised by the worker when it tries to execute a
    which there is not callback
    '''
    pass


class TaskAlreadyRegistered(Exception):
    '''It is raised when @task decorator or Kamma.add_task is being called with a task id already used.
    '''
    pass


class AbortTask(Exception):
    ''' Exception which can be raised by the callback in order to
    abort the executing task due to a decision taken by the application
    '''
    pass


class TimeoutTask(Exception):
    ''' Exception which can be raised internally in kamma when the
    callback lasts more time than its given 'timeout'
    '''
    pass


class RetryStopped(Exception):
    ''' When a task cannot be executed within limited retry policy
    '''

    def __init__(self, callback, attempts, delay, last_error):
        self.callback = callback
        self.attempts = attempts
        self.delay = delay
        self.last_error = last_error
        self.json_task = ""
        msg = "The task '{cb}' has failed after {tries} attempts and {sec} seconds. "\
            "Last Error: {err}".format(cb=callback, tries=attempts, sec=delay, err=last_error)
        super(RetryStopped, self).__init__(msg)
