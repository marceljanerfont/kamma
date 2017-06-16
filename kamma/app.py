# -*- encoding: utf-8 -*-
import sys
import os
import threading
import traceback
import logging
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import kamma
from kamma import task
from kamma.queue import FileQueue


logger = logging.getLogger(__name__)


class Kamma(object):
    def __init__(self, queue_path="task_queue"):
        self._quit = False
        self._thread = None
        self._exception = None
        self._on_failure = None
        self._on_abortion = None
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

    def task_callback(self, timeout=(4 * 60 * 60), retry_wait=task.wait_fixed(15), retry_stop=task.stop_none()):
        ''' Registers a Task callback in Kamma.
        '''
        def decorator(func):
            self.add_task_callback(callback=func, timeout=timeout, retry_wait=retry_wait, retry_stop=retry_stop)
            return func
        return decorator

    def on_failure(self):
        ''' Registers a on_failure callback in Kamma. It will be called each time that error occurs
        '''
        def decorator(func):
            self.add_on_failure(func)
            return func
        return decorator

    def on_abortion(self):
        ''' Registers a on_anortion callback in Kamma. It will be called each time that task is aborted
        '''
        def decorator(func):
            self.add_on_abortion(func)
            return func
        return decorator

    def add_task_callback(self, callback, timeout=(4 * 60 * 60), retry_wait=task.wait_fixed(15), retry_stop=task.stop_none()):
        ''' Registers a Task in Kamma.
        :param function callback: The name of the callback function has to be unique.
        '''
        if callback.__name__ in self._callbacks:
            raise kamma.TaskAlreadyRegistered('the task \'{}\' is already used'.format(callback.__name__))
        self._callbacks[callback.__name__] = task.TaskCallback(callback, timeout=timeout, retry_wait=retry_wait, retry_stop=retry_stop)

    def add_on_failure(self, callback):
        self._on_failure = callback

    def add_on_abortion(self, callback):
        self._on_abortion = callback

    def push_task(self, callback, **kwargs):
        logger.debug('push task \'{}\' with kwargs: {}'.format(callback.__name__, kwargs))
        with self._mutex:
            if callback.__name__ not in self._callbacks:
                raise kamma.TaskNotRegistered('the task \'{}\' is not registered'.format(callback.__name__))
            self._queue.push(json.dumps({'callback': callback.__name__, 'kwargs': kwargs}))
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
                if self._queue.length() > 0:
                    self._process_queue()
                self._push_event.wait(10)
        except Exception as e:
            logger.error(traceback.format_exc())
            with self._mutex:
                self._exception = e
                self._empty_event.set()
                raise self._exception
        finally:
            logger.info("exiting")

    def run_async(self):
        self._thread = threading.Thread(target=self.run, args=())
        self._thread.start()

    def _process_queue(self):
        count = 0
        while not self._quit and self._queue.length() > 0:
            json_task = self._queue.head()
            task_queued = json.loads(json_task)
            task_callback = self._get_task_callback(task_queued['callback'])
            task_kwargs = task_queued['kwargs']
            try:
                task_callback.execute(quit_event=self._quit_event, **task_kwargs)
                self._queue.pop()
            except kamma.AbortTask as e:
                logger.warning('AbortTask exception from \'{}\' due to: {}'.format(task_queued['callback'], e))
                if self._on_abortion:
                    self._on_abortion(json_task=json_task, reason=str(e))
                self._queue.pop()
            except kamma.RetryStopped as e:
                logger.warning('RetryStopped exception from \'{}\' due to: {}'.format(task_queued['callback'], e))
                if self._on_failure:
                    self._on_failure(json_task=json_task, retry_stopped=e)
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
    worker = Kamma(tasks=dict())
    worker.stop()
