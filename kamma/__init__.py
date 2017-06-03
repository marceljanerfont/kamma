# -*- encoding: utf-8 -*-

__version__ = '0.0.4'

import logging
from collections import namedtuple
try:
    # not available in python 2.6
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):

        def emit(self, record):
            pass

# Add NullHandler to prevent logging warnings
logging.getLogger(__name__).addHandler(NullHandler())

# class for Task definition
TaskCallback = namedtuple('TaskCallback', ['id', 'callback'])

# class to create an instance of a certain task type
Task = namedtuple('Task', ['id', 'data'])


class TaskNotRegistered(Exception):
    '''It can be raised by the worker when it tries to execute a
    which there is not callback
    '''
    pass


class AbortTask(Exception):
    ''' Exception which can be raised by the callback in order to
    abort the executing task due because the app considers it as invalid
    '''
    pass