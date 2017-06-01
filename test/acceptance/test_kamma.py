# -*- encoding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import sys
import os
# add kamma path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import kamma
from kamma import KammaWorker

TEST_PATH = "test_queue"
NUM_ITEMS = 50


class KammaTests(unittest.TestCase):
    def task0_ko(self, data):
        raise Exception('I don\'t want to work')

    def task0(self, data):
        print("task0 data: {}".format(data))
        self.assertEqual('task0', data['task_type'])

    def task1(self, data):
        print("task1 data: {}".format(data))
        self.assertEqual('task1', data['task_type'])

    def task2(self, data):
        print("task2 data: {}".format(data))
        self.assertEqual('task2', data['task_type'])

    def setUp(self):
        worker = KammaWorker(queue_path=TEST_PATH, interval_sec=10)
        print('++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ {}'.format(worker))
        worker.register_task(task_type='task0', task_callback=self.task0_ko)
        worker.register_task(task_type='task1', task_callback=self.task1)
        worker.register_task(task_type='task2', task_callback=self.task2)
        worker.push_task(task_type='task0', task_data={'task_type': 'task0'})
        for i in range(0, 10):
            worker.push_task(task_type='task1', task_data={'task_type': 'task1'})
            worker.push_task(task_type='task1', task_data={'task_type': 'task1'})
            worker.push_task(task_type='task2', task_data={'task_type': 'task2'})
            worker.push_task(task_type='task2', task_data={'task_type': 'task2'})
            worker.push_task(task_type='task1', task_data={'task_type': 'task1'})
            worker.push_task(task_type='task2', task_data={'task_type': 'task2'})
        # outage emulation
        worker.stop()
        worker = None

    def test_usual_case(self):
        worker2 = KammaWorker(queue_path=TEST_PATH, interval_sec=1)
        print('*********************************************************** {}'.format(worker2))
        worker2.register_task(task_type='task1', task_callback=self.task1)
        worker2.register_task(task_type='task2', task_callback=self.task2)
        #self.assertRaises(kamma.TaskNotRegistered, lambda: worker2.wait())
        worker2.register_task(task_type='task0', task_callback=self.task0)
        worker2.wait()
        worker2.stop()


if __name__ == '__main__':
    unittest.main()
