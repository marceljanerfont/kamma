# -*- encoding: utf-8 -*-
import sys
import os
import copy
import threading
import traceback
import logging
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import kamma
from kamma.queue import FileQueue


logger = logging.getLogger(__name__)


class KammaWorker(object):
    def __init__(self, tasks, queue_path="task_queue", retry_interval=15):
        self.retry_interval = max(1, retry_interval)
        self.quit = False
        self.thread = None
        self.exception = None
        self.mutex = threading.Lock()
        self.empty_event = threading.Event()
        self.push_event = threading.Event()
        self.quit_event = threading.Event()
        # maps of task types --> task callback
        self.tasks = copy.copy(tasks)
        self.queue = FileQueue(queue_path)
        # return self  # fluent pattern

    def __del__(self):
        self.stop()
        self.tasks = None
        self.queue = None

    def push_task(self, key, data):
        logger.debug('push task of type \'{}\' with data: {}'.format(key, data))
        with self.mutex:
            if not self._is_registered(key):
                raise kamma.TaskNotRegistered('the task \'{}\' is not registered'.format(key))
            self.queue.push(json.dumps({'type': key, 'data': data}))
            self.empty_event.clear()
            self.push_event.set()

    def stop(self):
        logger.info('stopping')
        with self.mutex:
            self.quit = True
            self.push_event.set()
            self.quit_event.set()
            if self.thread and self.thread.is_alive():
                self.thread.join()
        logger.info('stopped')

    def pending(self):
        return self.queue.length()

    def wait_empty_event(self, timeout=None):
        logger.info('waiting')
        self.empty_event.wait(timeout)
        if self.exception:
            e = self.exception
            self.exception = None
            raise e

    def _is_registered(self, key):
        return True if key in self.tasks else False

    def _get_callback(self, key):
        return self.tasks.get(key, None)

    def run(self):
        logger.info("running")
        try:
            while not self.quit:
                try:
                    self._process_queue()
                    self.push_event.wait(10)
                except kamma.TaskNotRegistered as e:
                    with self.mutex:
                        self.exception = e
                        self.empty_event.set()
                        raise self.exception
                except Exception:
                    logger.error(traceback.format_exc())
                    self.quit_event.wait(self.retry_interval)
        finally:
            logger.info("exiting")

    def run_async(self):
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.start()

    def _process_queue(self):
        count = 0
        while not self.quit and self.queue.length() > 0:
            task = json.loads(self.queue.head())
            key = task['type']
            callback = self._get_callback(key)
            if not callback:
                raise kamma.TaskNotRegistered('the task \'{}\' is not registered'.format(key))
            logger.debug('processing task: {}'.format(key))
            callback(task['data'])
            self.queue.pop()
            count = count + 1
        if count > 0:
            logger.info("processed {} queued tasks".format(count))
        with self.mutex:
            if self.queue.length() == 0:
                self.push_event.clear()
                self.empty_event.set()
                logger.debug("set empty event")


if __name__ == "__main__":
    worker = KammaWorker(tasks=dict())
    worker.stop()
