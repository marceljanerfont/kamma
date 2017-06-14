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
from kamma import task
from kamma.queue import FileQueue


_task = namedtuple('_task', ['callback', 'retry'])

logger = logging.getLogger(__name__)


class Kamma(object):
    def __init__(self, queue_path="task_queue", retry_interval=15):
        self._retry_interval = max(1, retry_interval)
        self._quit = False
        self._thread = None
        self._exception = None
        self._callbacks = dict()
        self._mutex = threading.Lock()
        self._empty_event = threading.Event()
        self._push_event = threading.Event()
        self._quit_event = threading.Event()
        self._queue = FileQueue(queue_path)

    def __del__(self):
        self.stop()
        self._callbacks = None
        self._queue = None

    def task_callback(self, id, timeout=(4 * 60 * 60), retry_wait=task.wait_fixed(15), retry_stop=task.stop_none()):
        ''' Registers a Task in Kamma.
        '''
        def decorator(func):
            self.add_task_callback(callback=func, timeout=timeout, retry_wait=retry_wait, retry_stop=retry_stop)
            return func
        return decorator

    def add_task_callback(self, callback, timeout=(4 * 60 * 60), retry_wait=task.wait_fixed(15), retry_stop=task.stop_none()):
        ''' Registers a Task in Kamma.
        :param function callback: The name of the callback function has to be unique.
        '''
        if callback.__name__ in self._callbacks:
            raise kamma.TaskAlreadyRegistered('the task \'{}\' is already used'.format(callback.__name__))
        self._callbacks[callback.__name__] = task.TaskCallback(callback, timeout=timeout, retry_wait=retry_wait, retry_stop=retry_stop)

    def push_task(self, callback, **kwargs):
        logger.debug('push task \'{}\' with kwargs: {}'.format(callback.callback, kwargs))
        with self._mutex:
            if callback.__name__ not in self._callbacks:
                raise kamma.TaskNotRegistered('the task \'{}\' is not registered'.format(callback.callback))
            self._queue.push(json.dumps({'callback': callback.callback, 'kwargs': kwargs}))
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

    def _get_task_callback(self, callback):
        if callback not in self._callbacks:
            raise kamma.TaskNotRegistered('the task \'{}\' is not registered'.format(callback))
        return self._callbacks.get(callback, None)

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
            task_callback = self._get_task_callback(task_queued['callback'])
            try:
                kwargs = task_queued['kwargs']
                task_callback.execute(quit_event=self._quit_event, **kwargs)
                self._queue.pop()
            except kamma.AbortTask as e:
                logger.warning('AbortTask exception from \'{}\' due to: {}'.format(task_queued['callback'], e))
                self._queue.pop()
                # TODO: save task in Abort folder
            except kamma.RetryStopped as e:
                logger.warning('RetryStopped exception from \'{}\' due to: {}'.format(task_queued['callback'], e))
                self._queue.pop()
                # TODO: save task in Failed folder
            count = count + 1
        if count > 0:
            logger.info("processed {} queued tasks".format(count))
        with self._mutex:
            if self._queue.length() == 0:
                self._push_event.clear()
                self._empty_event.set()
                logger.debug("set empty event")


if __name__ == "__main__":
    worker = Kamma(tasks=dict())
    worker.stop()
