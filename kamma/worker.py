# -*- encoding: utf-8 -*-
import sys
import os
import threading
import traceback
import logging
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import kamma
from kamma.queue import FileQueue


logger = logging.getLogger(__name__)


class KammaWorker(object):
    def __init__(self, task_callbacks, queue_path="task_queue", retry_interval=15):
        self._retry_interval = max(1, retry_interval)
        self._quit = False
        self._thread = None
        self._exception = None
        self._tasks = dict()
        self._mutex = threading.Lock()
        self._empty_event = threading.Event()
        self._push_event = threading.Event()
        self._quit_event = threading.Event()
        # maps of task types --> task callback
        for task in task_callbacks:
            self._tasks[task.id] = task.callback
        self._queue = FileQueue(queue_path)

    def __del__(self):
        self.stop()
        self._tasks = None
        self._queue = None

    def push_task(self, task):
        logger.debug('push task of type \'{}\' with data: {}'.format(task.id, task.data))
        with self._mutex:
            if not self._is_registered(task.id):
                raise kamma.TaskNotRegistered('the task \'{}\' is not registered'.format(task.id))
            self._queue.push(json.dumps({'id': task.id, 'data': task.data}))
            self._empty_event.clear()
            self._push_event.set()

    def stop(self):
        logger.info('stopping')
        with self._mutex:
            self._quit = True
            self._push_event.set()
            self._quit_event.set()
            if self._thread and self._thread.is_alive():
                self._thread.join()
        logger.info('stopped')

    def pending(self):
        return self._queue.length()

    def wait_empty_event(self, timeout=None):
        logger.info('waiting')
        self._empty_event.wait(timeout)
        if self._exception:
            e = self._exception
            self._exception = None
            raise e

    def _is_registered(self, task_id):
        return True if task_id in self._tasks else False

    def _get_callback(self, task_id):
        return self._tasks.get(task_id, None)

    def run(self):
        logger.info("running")
        try:
            while not self._quit:
                try:
                    self._process_queue()
                    self._push_event.wait(10)
                except kamma.TaskNotRegistered as e:
                    with self._mutex:
                        self._exception = e
                        self._empty_event.set()
                        raise self._exception
                except Exception:
                    logger.error(traceback.format_exc())
                    self._quit_event.wait(self._retry_interval)
        finally:
            logger.info("exiting")

    def run_async(self):
        self._thread = threading.Thread(target=self.run, args=())
        self._thread.start()

    def _process_queue(self):
        count = 0
        while not self._quit and self._queue.length() > 0:
            task = json.loads(self._queue.head())
            task_id = task['id']
            callback = self._get_callback(task_id)
            if not callback:
                raise kamma.TaskNotRegistered('the task \'{}\' is not registered'.format(task_id))
            logger.debug('processing task: {}'.format(task_id))
            try:
                callback(task['data'])
                self._queue.pop()
            except kamma.AbortTask as e:
                logger.info('received AbortTask exception from \'{}\' due to: {}'.format(task_id, e))
                self._queue.pop()
            count = count + 1
        if count > 0:
            logger.info("processed {} queued tasks".format(count))
        with self._mutex:
            if self._queue.length() == 0:
                self._push_event.clear()
                self._empty_event.set()
                logger.debug("set empty event")


if __name__ == "__main__":
    worker = KammaWorker(tasks=dict())
    worker.stop()
