# -*- encoding: utf-8 -*-
import sys
from collections import namedtuple
import multiprocessing
import logging
import kamma

try:
    MAX_WAIT = sys.maxint / 2
except AttributeError:
    MAX_WAIT = 1073741823


logger = logging.getLogger(__name__)

""" task to be done."""
exec_info = namedtuple('exec_info', ['attempts', 'delay'])


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


# task is a piece of work to be done
class TaskCallback(object):
    """Task definition by it 'id', callback, timeout in seconds, retry wait and retry stop.
    WARNING: callbacks cannot be nested functions (python in windows)
    """

    def __init__(self, callback, timeout, retry_wait, retry_stop):
        self._callback = callback
        self._timeout = timeout
        self._retry_wait = retry_wait
        self._retry_stop = retry_stop

    def execute(self, quit_event, **kwargs):
        previous_attempt_number = 0
        delay_since_first_attempt = 0
        last_error = ""
        while not self._retry_stop(previous_attempt_number, delay_since_first_attempt):
            logger.debug("Executing task '{cb}' try: {attempt} total wait: {delay}".format(cb=self._callback.__name__,
                                                                                           attempt=previous_attempt_number + 1,
                                                                                           delay=delay_since_first_attempt))
            try:
                if self._execute(**kwargs):
                    return exec_info(attempts=previous_attempt_number + 1, delay=delay_since_first_attempt)
            except kamma.AbortTask as e:
                raise e
            except Exception as e:
                last_error = str(e)
                logger.warning("Exception running task '{cb}': {e}".format(cb=self._callback.__name__, e=last_error))
            wait = self._retry_wait(previous_attempt_number, delay_since_first_attempt)
            quit_event.wait(wait)
            previous_attempt_number += 1
            delay_since_first_attempt += wait
        raise kamma.RetryStopped(callback=self._callback.__name__,
                                 attempts=previous_attempt_number,
                                 delay=delay_since_first_attempt,
                                 last_error=last_error)

    def _execute(self, **kwargs):
        # Start bar as a process
        # concurrent.futures were introduced in python 3.2
        exception_queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=self._run_callback, args=(self._callback, exception_queue,), kwargs=kwargs)
        # p.daemon = True
        p.start()

        # Wait for self._timoeut seconds or until process finishes
        p.join(self._timeout)

        # If thread is still active
        if p.is_alive():
            # Terminate
            p.terminate()
            p.join()
            raise kamma.TimeoutTask("Timeout triggered after {sec} seconds.".format(sec=self._timeout))
        # process child exception
        if not exception_queue.empty():
            raise exception_queue.get_nowait()
        logger.debug("Task '{cb}' executed successfully".format(cb=self._callback.__name__))
        return True

    def _run_callback(self, callback, exception_queue, **kwargs):
        try:
            callback(**kwargs)
        except Exception as e:
            exception_queue.put(e)
