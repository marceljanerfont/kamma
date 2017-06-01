# -*- encoding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from kamma.file_queue import FileQueue
from copy import deepcopy
import threading
import traceback
import logging
import time
import json

__version__ = '0.0.1'


logger = logging.getLogger("kamma")


class TaskNotRegistered(Exception):
    pass


class KammaWorker(object):
    def __init__(self, tasks=dict(), queue_path="task_queue", interval_sec=15):
        self.interval_sec = max(1, interval_sec)
        self.quit = False
        self.mutex = threading.Lock()
        self.exception = None
        self.empty_event = threading.Event()
        # maps of task types --> task callback
        self.tasks = deepcopy(tasks)
        self.queue = FileQueue(queue_path)
        self.thread = threading.Thread(target=self._run, args=())
        self.thread.start()

    def __del__(self):
        self.stop()
        self.tasks = None
        self.queue = None

    def register_task(self, task_type, task_callback):
        self.mutex.acquire()
        try:
            self.tasks[task_type] = task_callback
            print("register tasks: {}".format(self.tasks))
        finally:
            self.mutex.release()

    def push_task(self, task_type, task_data):
        logger.debug('push task of type \'{}\' with data: {}'.format(task_type, task_data))
        if not self._is_registered(task_type):
            raise TaskNotRegistered('the task \'{}\' is not registered'.format(task_type))
        self.queue.push(json.dumps({'type': task_type, 'data': task_data}))
        self.empty_event.clear()

    def stop(self):
        logger.info('stopping')
        self.quit = True
        self.thread.join()
        logger.info('stopped')

    def wait(self, timeout=None):
        self.empty_event.wait(timeout)
        if self.exception:
            raise self.exception

    def _is_registered(self, task_type):
        self.mutex.acquire()
        try:
            return True if task_type in self.tasks else False
        finally:
            self.mutex.release()

    def _get_callback(self, task_type):
        self.mutex.acquire()
        try:
            return self.tasks.get(task_type, None)
        finally:
            self.mutex.release()

    def _run(self):
        logger.info("running")
        try:
            while not self.quit:
                try:
                    self._process_queue()
                    if self.queue.length() == 0:
                        self.empty_event.set()
                    # wait cadence
                    for i in range(self.interval_sec):
                        if self.quit:
                            break
                        time.sleep(1)
                except TaskNotRegistered as e:
                    self.exception = e
                    self.empty_event.set()
                except Exception:
                    logger.error(traceback.format_exc())
                    for i in range(self.interval_sec):
                        if self.quit:
                            break
                        time.sleep(1)
        finally:
            logger.info("exiting")

    def _process_queue(self):
        task_str = self.queue.head()
        count = 0
        while task_str and not self.quit:
            task = json.loads(task_str)
            task_type = task['type']
            task_callback = self._get_callback(task_type)
            if not task_callback:
                raise TaskNotRegistered('the task \'{}\' is not registered'.format(task_type))
            logger.debug('processing task: {}'.format(task_type))
            task_callback(task['data'])
            self.queue.pop()
            count = count + 1
            task_str = self.queue.head()
        logger.info("processed {} queued tasks".format(count))


if __name__ == "__main__":
    worker = KammaWorker()
    worker.stop()
