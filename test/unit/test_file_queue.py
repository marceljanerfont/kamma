try:
    import unittest2 as unittest
except ImportError:
    import unittest

import sys
import os

# add kamma path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from kamma.file_queue import FileQueue


TEST_PATH = "test_queue"
NUM_ITEMS = 50


class EnqueueTests(unittest.TestCase):
    def setUp(self):
        queue = FileQueue(TEST_PATH)
        while queue.length():
            queue.pop()

    def tearDown(self):
        queue = FileQueue(TEST_PATH)
        while queue.length():
            queue.pop()

    def test_enqueue(self):
        queue = FileQueue(TEST_PATH)
        length = queue.length()
        for i in range(length, length + NUM_ITEMS):
            queue.push("{0:05d}".format(i))
        self.assertEqual(NUM_ITEMS, queue.length())
        queue = None


class DequeueTests(unittest.TestCase):
    def setUp(self):
        queue = FileQueue(TEST_PATH)
        while queue.length():
            queue.pop()
        for i in range(0, NUM_ITEMS):
            queue.push("{0:05d}".format(i))
        self.assertEqual(NUM_ITEMS, queue.length())

    def tearDown(self):
        queue = FileQueue(TEST_PATH)
        while queue.length():
            queue.pop()

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
        queue = FileQueue(TEST_PATH)
        while queue.length():
            queue.pop()

    def tearDown(self):
        queue = FileQueue(TEST_PATH)
        while queue.length():
            queue.pop()

    def test_enqueue_dequeue(self):
        queue = FileQueue(TEST_PATH)
        length = queue.length()
        for i in range(length, length + NUM_ITEMS):
            queue.push("{0:05d}".format(i))
        self.assertEqual(NUM_ITEMS, queue.length())
        queue = None

        queue = FileQueue(TEST_PATH)
        length = queue.length()
        for i in range(length, length + NUM_ITEMS):
            queue.push("{0:05d}".format(i))
        self.assertEqual(NUM_ITEMS + NUM_ITEMS, queue.length())
        queue = None

        queue = FileQueue(TEST_PATH)
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

        queue = FileQueue(TEST_PATH)
        counter = 0
        while queue.length():
            item = queue.pop()
            if not item:
                break
            self.assertEqual(counter + NUM_ITEMS, int(item))
            counter = counter + 1
        self.assertEqual(NUM_ITEMS, counter)
        self.assertEqual(0, queue.length())
        queue = None


if __name__ == '__main__':
    unittest.main()
