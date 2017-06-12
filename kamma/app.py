# -*- encoding: utf-8 -*-
import sys
import os
from collections import namedtuple
import multiprocessing
import threading
import traceback
import logging
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import kamma
from kamma import Retry, wait_fixed
from kamma.queue import FileQueue


_task = namedtuple('_task', ['callback', 'retry'])

logger = logging.getLogger(__name__)


class Kamma(object):
    def __init__(self, queue_path="task_queue", retry_interval=15):
        self._retry_interval = max(1, retry_interval)
        self._quit = False
        self._thread = None
        self._exception = None
        self._tasks = dict()
        self._mutex = threading.Lock()
        self._empty_event = threading.Event()
        self._push_event = threading.Event()
        self._quit_event = threading.Event()
        self._queue = FileQueue(queue_path)

    def __del__(self):
        self.stop()
        self._tasks = None
        self._queue = None

    def task_callback(self, id, timeout=, retry_wait, retry_stop):
        ''' Registers a Task in Kamma.
        :param str id: It is the task identifier and should be unique.
        '''
        def decorator(func):
            self.add_task(id=id, callback=func, retry=retry)
            return func
        return decorator

    def add_task_callback(self, id, callback, retry=Retry(wait=wait_fixed(15), stopper=None)):
        ''' Registers a Task in Kamma.
        :param str id: It is the task identifier and should be unique.
        '''
        if id in self._tasks:
            raise kamma.TaskAlreadyRegistered('the task id \'{}\' is already used'.format(id))
        self._tasks[id] = _task(callback, retry)

    def push_task(self, task):
        logger.debug('push task of type \'{}\' with data: {}'.format(task.id, task.data))
        with self._mutex:
            if not self._is_registered(task.id):
                raise kamma.TaskNotRegistered('the task \'{}\' is not registered'.format(task.id))
            self._queue.push(json.dumps({'id': task.id, 'data': task.data}))
            self._empty_event.clear()
            self._push_event.set()

    def stop(self):
        with self._mutex:
            self._quit = True
            self._push_event.set()
            self._quit_event.set()
            if self._thread and self._thread.is_alive():
                logger.info('stopping')
                self._thread.join()
                logger.info('stopped')

    def pending(self):
        return self._queue.length()

    def wait_empty_event(self, timeout=None):
        logger.info('waiting')
        if self._queue.length() == 0:
            self._empty_event.set()
        self._empty_event.wait(timeout)
        if self._exception:
            e = self._exception
            self._exception = None
            raise e

    def _is_registered(self, id):
        return True if id in self._tasks else False

    def _get_callback(self, id):
        return self._tasks.get(id, _task(None, None)).callback

    def _get_task(self, id):
        if not self._is_registered(id):
            raise kamma.TaskNotRegistered('the task \'{}\' is not registered'.format(id))
        return self._tasks.get(id, None)

    def run(self):
        logger.info("running")
        try:
            while not self._quit:
                try:
                    if self._queue.length() > 0:
                        self._process_queue()
                    self._push_event.wait(10)
                except kamma.TaskNotRegistered as e:
                    with self._mutex:
                        self._exception = e
                        self._empty_event.set()
                        raise self._exception
                except Exception:
                    logger.error(traceback.format_exc())
        finally:
            logger.info("exiting")

    def run_async(self):
        self._thread = threading.Thread(target=self.run, args=())
        self._thread.start()

    def _process_queue(self):
        count = 0
        while not self._quit and self._queue.length() > 0:
            task_queued = json.loads(self._queue.head())
            task = self._get_task(task_queued['id'])
            try:
                self._process_task(task, task_queued['data'])
                self._queue.pop()
            except kamma.AbortTask as e:
                logger.info('received AbortTask exception from \'{}\' due to: {}'.format(task.id, e))
                self._queue.pop()
            except kamma.RetryStopped as e:
                logger.warning('received RetryStopped exception from \'{}\' due to: {}'.format(task_id, e))
                self._queue.pop()

            count = count + 1
        if count > 0:
            logger.info("processed {} queued tasks".format(count))
        with self._mutex:
            if self._queue.length() == 0:
                self._push_event.clear()
                self._empty_event.set()
                logger.debug("set empty event")

    def _process_task(self, task, task_data):
        logger.debug('processing task: {}'.format(task.id))
        retry = task.retry
        stop = False
        while not self._quit and not stop:
            try:
                task.callback(task_data)
                self._queue.pop()
            except kamma.AbortTask as e:
                raise e
            except Exception:
                logger.warning(traceback.format_exc())
                # wait retry
            self._quit_event.wait(self._retry_interval)



if __name__ == "__main__":
    worker = Kamma(tasks=dict())
    worker.stop()
