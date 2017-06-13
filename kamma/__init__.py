# -*- encoding: utf-8 -*-
import logging

__version__ = '0.0.6'

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


class RetryStopped(Exception):
    ''' When a task cannot be executed within limited retry policy
    '''
    pass
