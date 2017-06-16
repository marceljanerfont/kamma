# -*- encoding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from multiprocessing import Manager
from random import randint
import logging
import sys
import os
import copy
import shutil
# add kamma path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import kamma

TEST_PATH = "test_queue"


handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)-8s] [%(name)-10s] [%(lineno)-4d] %(message)s'))
logger_kamma = logging.getLogger('kamma.app')
logger_kamma.handlers = [handler]
# logger_kamma.setLevel(logging.DEBUG)
logger_fqueue = logging.getLogger('kamma.queue')
logger_fqueue.handlers = [handler]
# logger_fqueue.setLevel(logging.DEBUG)
logger_task = logging.getLogger('kamma.task')
logger_task.handlers = [handler]
# logger_task.setLevel(logging.DEBUG)
logger = logging.getLogger('test')
logger.handlers = [handler]
logger.setLevel(logging.DEBUG)


def _clear_queue():
    try:
        shutil.rmtree(TEST_PATH)
    except Exception:
        pass


# it should be out of the class scope, otherwise
# python tries to pickle all class and its manager and then
# the serialization will fail
the_manager = None


class KammaTestsCheckOrder(unittest.TestCase):
    def setUp(self):
        _clear_queue()
        self.callbacks = [self.task0, self.task1, self.task2, self.task3, self.task4, self.task5]
        # Manager is necessary because it is modified from different threads
        the_manager = Manager()
        self.cb_indexs = the_manager.list()
        for i in range(0, 100):
            self.cb_indexs.append(randint(0, 5))

    def tearDown(self):
        _clear_queue()

    def _taskx(self, task_id, data):
        logger.debug("running '{}', remaining {} tasks".format(task_id, len(self.cb_indexs)))
        self.assertEqual(task_id, data['id'], "{} data: {}, tasks: {}".format(task_id, data, self.cb_indexs))
        self.assertEqual(task_id, self.callbacks[self.cb_indexs[0]].__name__)
        self.cb_indexs.pop(0)

    def task0(self, data):
        self._taskx('task0', data)

    def task1(self, data):
        self._taskx('task1', data)

    def task2(self, data):
        self._taskx('task2', data)

    def task3(self, data):
        self._taskx('task3', data)

    def task4(self, data):
        self._taskx('task4', data)

    def task5(self, data):
        self._taskx('task5', data)

    def test_usual_case(self):
        worker = kamma.Kamma(queue_path=TEST_PATH)
        worker.add_task_callback(callback=self.task0, retry_wait=kamma.wait_fixed(0), retry_stop=kamma.stop_after_attempt(1))
        worker.add_task_callback(callback=self.task1, retry_wait=kamma.wait_fixed(0), retry_stop=kamma.stop_after_attempt(1))
        worker.add_task_callback(callback=self.task2, retry_wait=kamma.wait_fixed(0), retry_stop=kamma.stop_after_attempt(1))
        worker.add_task_callback(callback=self.task3, retry_wait=kamma.wait_fixed(0), retry_stop=kamma.stop_after_attempt(1))
        worker.add_task_callback(callback=self.task4, retry_wait=kamma.wait_fixed(0), retry_stop=kamma.stop_after_attempt(1))
        worker.add_task_callback(callback=self.task5, retry_wait=kamma.wait_fixed(0), retry_stop=kamma.stop_after_attempt(1))
        cloned_cb_indexs = copy.deepcopy(self.cb_indexs)
        worker.run_async()
        for i in cloned_cb_indexs:
            worker.push_task(callback=self.callbacks[i], data={'id': self.callbacks[i].__name__})
        worker.wait_empty_event()
        self.assertEqual(0, worker.pending())
        worker.stop()
        self.assertEqual(0, len(self.cb_indexs))


class KammaTestsExceptionsInKamma(unittest.TestCase):
    def setUp(self):
        _clear_queue()

    def tearDown(self):
        _clear_queue()

    def task(self):
        pass

    def test_exception_pushtask_TaskNotRegistered(self):
        worker = kamma.Kamma(queue_path=TEST_PATH)
        self.assertRaises(kamma.TaskNotRegistered, lambda: worker.push_task(callback=self.task))
        # worker.wait()
        worker.stop()


class KammaTestsExceptionsInTask(unittest.TestCase):
    def setUp(self):
        _clear_queue()
        the_manager = Manager()
        self.count = the_manager.list()
        self.count.append(0)
        self.num_failures = 3

    def tearDown(self):
        _clear_queue()

    def task0(self):
        self.count[0] = self.count[0] + 1
        if self.count[0] < self.num_failures:
            raise Exception('I don\'t want to work, try {}'.format(self.count[0]))

    def test_exception_in_task(self):
        worker = kamma.Kamma(queue_path=TEST_PATH)
        worker.add_task_callback(callback=self.task0, retry_wait=kamma.wait_fixed(0), retry_stop=kamma.stop_after_attempt(self.num_failures+1))
        worker.push_task(callback=self.task0)
        worker.run_async()
        worker.wait_empty_event()
        worker.stop()
        self.assertEqual(self.num_failures, self.count[0])


class KammaTestsOnAbortion(unittest.TestCase):
    def setUp(self):
        _clear_queue()
        self.abortion_called = False
        self.failure_called = False

    def tearDown(self):
        _clear_queue()

    def task_abort(self):
        raise kamma.AbortTask("I'm indisposed")

    def task_failure(self):
        raise Exception("Boom")

    def on_abortion(self, json_task, reason):
        self.abortion_called = True

    def on_failure(self, json_task, retry_stopped):
        self.failure_called = True

    def test_on_abortion(self):
        worker = kamma.Kamma(queue_path=TEST_PATH)
        worker.add_on_abortion(self.on_abortion)
        worker.add_task_callback(self.task_abort)
        worker.run_async()
        worker.push_task(self.task_abort)
        worker.wait_empty_event()
        worker.stop()
        self.assertTrue(self.abortion_called)

    def test_on_failure(self):
        worker = kamma.Kamma(queue_path=TEST_PATH)
        worker.add_on_failure(self.on_failure)
        worker.add_task_callback(self.task_failure, retry_wait=kamma.wait_fixed(0), retry_stop=kamma.stop_after_attempt(1))
        worker.run_async()
        worker.push_task(self.task_failure)
        worker.wait_empty_event()
        worker.stop()
        self.assertTrue(self.failure_called)


if __name__ == '__main__':
    unittest.main()
