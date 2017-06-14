try:
    import unittest2 as unittest
except ImportError:
    import unittest

import threading
import logging
import time
import sys
import os

# add kamma path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import kamma
from kamma import task


handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)-8s] [%(name)-10s] [%(lineno)-4d] %(message)s'))
logger_task = logging.getLogger('kamma.task')
logger_task.handlers = [handler]
logger_task.setLevel(logging.DEBUG)
logger = logging.getLogger('test_task_cb')
logger.handlers = [handler]
logger.setLevel(logging.DEBUG)


class TaskTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    # callbacks cannot be a nested functions
    def callback_ok(self, a, b, c):
        logger.debug("this is the '{cb}', a: {a}, b: {b}, c: {c}".format(cb=__name__, a=a, b=b, c=c))

    def callback_ko(self, a, b, c):
        logger.debug("this is the '{cb}', a: {a}, b: {b}, c: {c}".format(cb=__name__, a=a, b=b, c=c))
        raise Exception("boom!")

    def callback_2sec(self, a, b, c):
        logger.debug("starting '{cb}', a: {a}, b: {b}, c: {c}".format(cb=__name__, a=a, b=b, c=c))
        time.sleep(2)
        logger.debug("callback done")

    def callback_abort(self, a, b, c):
        logger.debug("this is the '{cb}', a: {a}, b: {b}, c: {c}".format(cb=__name__, a=a, b=b, c=c))
        raise kamma.AbortTask("I'm lazy")

    def test_execute(self):
        quit_event = threading.Event()
        tc = task.TaskCallback(callback=self.callback_ok,
                               timeout=1,
                               retry_wait=task.wait_fixed(15),
                               retry_stop=task.stop_none())
        tc.execute(quit_event, a=1, b=2, c=3)

    def test_execute_retry_stop(self):
        quit_event = threading.Event()
        tc = task.TaskCallback(callback=self.callback_ko,
                               timeout=1,
                               retry_wait=task.wait_fixed(2),
                               retry_stop=task.stop_after_attempt(1))
        try:
            tc.execute(quit_event, a=1, b=2, c=3)
            self.assertTrue(False, "The raised excpetion should be of type 'kamma.RetryStopped'.")
        except kamma.RetryStopped as e:
            self.assertEqual(e.attempts, 1)
            self.assertEqual(e.delay, 2)
        except Exception as e:
            self.assertTrue(False, "The raised excpetion should be of type 'kamma.RetryStopped'."
                                   "Received Exception: {}".format(str(e)))

    def test_execute_timeout_retry_stop(self):
        quit_event = threading.Event()
        tc = task.TaskCallback(callback=self.callback_2sec,
                               timeout=1,
                               retry_wait=task.wait_fixed(2),
                               retry_stop=task.stop_after_attempt(2))
        try:
            tc.execute(quit_event, a=1, b=2, c=3)
            self.assertTrue(False, "The raised excpetion should be of type 'kamma.RetryStopped'.")
        except kamma.RetryStopped as e:
            self.assertEqual(e.attempts, 2)
            self.assertEqual(e.delay, 4)
        except Exception as e:
            self.assertTrue(False, "The raised excpetion should be of type 'kamma.RetryStopped'. \
                                    Received Exception: {}".format(str(e)))

    def test_execute_aborted(self):
        quit_event = threading.Event()
        tc = task.TaskCallback(callback=self.callback_abort,
                               timeout=1,
                               retry_wait=task.wait_fixed(2),
                               retry_stop=task.stop_after_attempt(1))

        self.assertRaises(kamma.AbortTask,
                          lambda: tc.execute(quit_event, a=1, b=2, c=3))


if __name__ == '__main__':
    unittest.main()
