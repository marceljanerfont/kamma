# -*- encoding: utf-8 -*-
import sys
import os
import copy
import threading
import traceback
import logging
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import kamma
from kamma.queue import FileQueue


logger = logging.getLogger(__name__)


class KammaWorker(object):
    def __init__(self, tasks, queue_path="task_queue", interval_sec=15):
        self.interval_sec = max(1, interval_sec)
        self.quit = False
        self.thread = None
        self.mutex = threading.Lock()
        self.exception = None
        self.empty_event = threading.Event()
        # maps of task types --> task callback
        self.tasks = copy.copy(tasks)
        self.queue = FileQueue(queue_path)
        self.thread = threading.Thread(target=self._run, args=())
        self.thread.start()

    def __del__(self):
        self.stop()
        self.tasks = None
        self.queue = None

    def push_task(self, key, data):
        logger.debug('push task of type \'{}\' with data: {}'.format(key, data))
        if not self._is_registered(key):
            raise kamma.TaskNotRegistered('the task \'{}\' is not registered'.format(key))
        self.queue.push(json.dumps({'type': key, 'data': data}))
        self.empty_event.clear()

    def stop(self):
        logger.info('stopping')
        self.quit = True
        if self.thread and self.thread.is_alive():
            self.thread.join()
        logger.info('stopped')

    def wait(self, timeout=None):
        self.empty_event.wait(timeout)
        if self.exception:
            e = self.exception
            self.exception = None
            raise e

    def _is_registered(self, key):
        self.mutex.acquire()
        try:
            return True if key in self.tasks else False
        finally:
            self.mutex.release()

    def _get_callback(self, key):
        self.mutex.acquire()
        try:
            return self.tasks.get(key, None)
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
                except kamma.TaskNotRegistered as e:
                    self.exception = e
                    self.empty_event.set()
                    raise self.exception
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
            key = task['type']
            callback = self._get_callback(key)
            if not callback:
                raise kamma.TaskNotRegistered('the task \'{}\' is not registered'.format(key))
            logger.debug('processing task: {}'.format(key))
            callback(task['data'])
            self.queue.pop()
            count = count + 1
            task_str = self.queue.head()
        if count > 0:
            logger.info("processed {} queued tasks".format(count))


if __name__ == "__main__":
    worker = KammaWorker()
    worker.stop()
