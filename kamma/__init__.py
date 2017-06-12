# -*- encoding: utf-8 -*-
import sys
import logging

__version__ = '0.0.6'

try:
    # not available in python 2.6
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):

        def emit(self, record):
            pass

try:
    MAX_WAIT = sys.maxint / 2
except AttributeError:
    MAX_WAIT = 1073741823

# Add NullHandler to prevent logging warnings
logging.getLogger(__name__).addHandler(NullHandler())


class stop_none(object):
    """Non stop strategy."""
    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        return False


class stop_after_attempt(object):
    """Stop strategy that stops when the previous attempt >= max_attempt."""

    def __init__(self, max_attempt_number):
        self.max_attempt_number = max_attempt_number

    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        return previous_attempt_number >= self.max_attempt_number


class stop_after_delay(object):
    """Stop strategy that stops when the time from the first attempt >= limit."""

    def __init__(self, max_delay):
        self.max_delay = max_delay

    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        return delay_since_first_attempt >= self.max_delay


class wait_fixed(object):
    """Wait strategy that waits a fixed amount of time between each retry."""
    def __init__(self, wait):
        self.wait_fixed = wait

    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        return self.wait_fixed


class wait_incremental(object):
    """Wait an incremental amount of time after each attempt.
    Starting at a starting value and incrementing by a value for each attempt
    (and restricting the upper limit to some maximum value).
    """

    def __init__(self, start=0, increment=100, max=MAX_WAIT):
        self.start = start
        self.increment = increment
        self.max = max

    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        result = self.start + (self.increment * previous_attempt_number)
        return max(0, min(result, self.max))


class wait_exponential(object):
    """Wait strategy that applies exponential backoff.
    It allows for a customized multiplier and an ability to restrict the
    upper limit to some maximum value.
    """
    def __init__(self, exp_base=2, multiplier=1, max=MAX_WAIT):
        self.multiplier = multiplier
        self.exp_base = exp_base
        self.max = max

    def __call__(self, previous_attempt_number, delay_since_first_attempt):
        try:
            exp = self.exp_base ** previous_attempt_number
            result = self.multiplier * exp
        except OverflowError:
            return self.max
        return max(0, min(result, self.max))


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
