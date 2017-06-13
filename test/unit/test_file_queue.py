try:
    import unittest2 as unittest
except ImportError:
    import unittest

import logging
import shutil
import sys
import os

# add kamma path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import kamma
from kamma.queue import FileQueue


handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)-8s] [%(name)-10s] [%(lineno)-4d] %(message)s'))
logger_fqueue = logging.getLogger('kamma.file_queue')
logger_fqueue.handlers = [handler]
logger_fqueue.setLevel(logging.DEBUG)


TEST_PATH = "test_queue"
NUM_ITEMS = 50


def _clear_queue():
    try:
        shutil.rmtree(TEST_PATH)
    except Exception:
        pass


class EnqueueTests(unittest.TestCase):
    def setUp(self):
        _clear_queue()

    def tearDown(self):
        _clear_queue()

    def test_enqueue(self):
        queue = FileQueue(TEST_PATH)
        length = queue.length()
        for i in range(length, length + NUM_ITEMS):
            queue.push("{0:05d}".format(i))
        self.assertEqual(NUM_ITEMS, queue.length())
        queue = None


class DequeueTests(unittest.TestCase):
    def setUp(self):
        _clear_queue()
        queue = FileQueue(TEST_PATH)
        for i in range(0, NUM_ITEMS):
            queue.push("{0:05d}".format(i))
        self.assertEqual(NUM_ITEMS, queue.length())

    def tearDown(self):
        _clear_queue()

    def test_dequeue(self):
        queue = FileQueue(TEST_PATH)
        counter = 0
        while queue.length():
            item = queue.pop()
            if not item:
                break
            self.assertEqual(counter, int(item))
            counter = counter + 1
        self.assertEqual(NUM_ITEMS, counter)
        queue = None


class EnqueueDequeueTests(unittest.TestCase):
    def setUp(self):
        _clear_queue()

    def tearDown(self):
        _clear_queue()

    def test_enqueue_dequeue(self):
        # enqueue NUM_ITEMS
        queue = FileQueue(TEST_PATH)
        length = queue.length()
        for i in range(length, length + NUM_ITEMS):
            queue.push("{0:05d}".format(i))
        self.assertEqual(NUM_ITEMS, queue.length())
        queue = None

        # enqueue NUM_ITEMS
        queue = FileQueue(TEST_PATH)
        length = queue.length()
        for i in range(length, length + NUM_ITEMS):
            queue.push("{0:05d}".format(i))
        self.assertEqual(NUM_ITEMS + NUM_ITEMS, queue.length())
        queue = None

        # dequeue NUM_ITEMS
        queue = FileQueue(TEST_PATH, max_head_index=-1)
        counter = 0
        while counter < NUM_ITEMS:
            item = queue.pop()
            if not item:
                break
            self.assertEqual(counter, int(item))
            counter = counter + 1
        self.assertEqual(NUM_ITEMS, counter)
        self.assertEqual(NUM_ITEMS, queue.length())
        queue = None

        # enqueue NUM_ITEMS
        queue = FileQueue(TEST_PATH, max_head_index=-1)
        length = queue.length()
        for i in range(length, length + NUM_ITEMS):
            queue.push("{0:05d}".format(i + NUM_ITEMS))
        self.assertEqual(NUM_ITEMS + NUM_ITEMS, queue.length())
        queue = None

        # dequeue
        queue = FileQueue(TEST_PATH, max_head_index=-1)
        counter = 0
        while queue.length():
            item = queue.pop()
            if not item:
                break
            self.assertEqual(counter + NUM_ITEMS, int(item))
            counter = counter + 1
        self.assertEqual(NUM_ITEMS + NUM_ITEMS, counter)
        self.assertEqual(0, queue.length())
        queue = None


'''
TODO:

* rotation
'''


if __name__ == '__main__':
    unittest.main()
