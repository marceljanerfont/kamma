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
from kamma.worker import KammaWorker

TEST_PATH = "test_queue"


handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)-8s] [%(name)-10s] [%(lineno)-4d] %(message)s'))
logger_kamma = logging.getLogger('kamma.worker')
logger_kamma.handlers = [handler]
logger_kamma.setLevel(logging.DEBUG)
logger_fqueue = logging.getLogger('kamma.queue')
logger_fqueue.handlers = [handler]
logger_fqueue.setLevel(logging.DEBUG)
logger = logging.getLogger('test')
logger.handlers = [handler]
logger.setLevel(logging.DEBUG)


def _clear_queue():
    try:
        shutil.rmtree(TEST_PATH)
    except Exception:
        pass


class KammaTestsCheckOrder(unittest.TestCase):
    def setUp(self):
        _clear_queue()
        # Manager is necessary because it is modified from different threads
        self.manager = Manager()
        self._tasks = self.manager.list()
        for i in range(0, 300):
            self._tasks.append(u'task{}'.format(randint(0, 5)))
        logger.debug("tasks: {}".format(self._tasks))

    def tearDown(self):
        _clear_queue()

    def _taskx(self, task, data):
        logger.debug("{} data: {}, tasks[0]: {}".format(task, data, self._tasks[0]))
        self.assertEqual(task, data['key'])
        self.assertEqual(task, self._tasks[0])
        self._tasks.pop(0)
        logger.debug("tasks: {}".format(self._tasks))

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
        worker = KammaWorker(
            queue_path=TEST_PATH,
            retry_interval=10,
            tasks=dict(
                task0=self.task0, task1=self.task1,
                task2=self.task2, task3=self.task3,
                task4=self.task4, task5=self.task5))
        # clone before since during the running the task list will be poped
        cloned_tasks = copy.deepcopy(self._tasks)
        worker.run_async()
        for task in cloned_tasks:
            worker.push_task(key=task, data={'key': task})
        worker.wait_empty_event()
        self.assertEqual(0, worker.pending())
        worker.stop()
        logger.debug("tasks: {}".format(self._tasks))
        self.assertEqual(0, len(self._tasks))


class KammaTestsExceptionsInKamma(unittest.TestCase):
    def setUp(self):
        _clear_queue()

    def tearDown(self):
        _clear_queue()

    def test_exception_pushtask_TaskNotRegistered(self):
        worker = KammaWorker(
            queue_path=TEST_PATH,
            tasks={},
            retry_interval=1)
        self.assertRaises(kamma.TaskNotRegistered, lambda: worker.push_task(key='task3', data={'key': 'task3'}))
        # worker.wait()
        worker.stop()


class KammaTestsExceptionsInTask(unittest.TestCase):
    def setUp(self):
        _clear_queue()
        self.count = 0
        self.num_failures = 3

    def tearDown(self):
        _clear_queue()

    def task0(self, data):
        self.count = self.count + 1
        if self.count < self.num_failures:
            raise Exception('I don\'t want to work {}'.format(self.count))

    def test_exception_in_task(self):
        worker = KammaWorker(
            queue_path=TEST_PATH,
            retry_interval=1,
            tasks=dict(task0=self.task0))
        worker.push_task(key='task0', data={'key': 'task0'})
        worker.run_async()
        worker.wait_empty_event()
        worker.stop()
        self.assertEqual(self.num_failures, self.count)


if __name__ == '__main__':
    unittest.main()
