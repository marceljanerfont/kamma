from collections import namedtuple

Task = namedtuple('Task', ['id', 'data'])


# task is a piece of work to be done
class TaskCallback(object):
    def __init__(self, id, callback, timeout, retry_wait, retry_stop):
        self._id = id
        self._callback = callback
        self._timoeut = timeout
        self._retry_wait = retry_wait
        self._retry_stop = retry_stop
