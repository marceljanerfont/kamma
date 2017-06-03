
# -*- encoding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import kamma
from kamma.worker import KammaWorker
import logging

try:
   input = raw_input
except NameError:
   pass

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)-8s] [%(name)-10s] [%(lineno)-4d] %(message)s'))
logger_kamma = logging.getLogger('kamma.worker')
logger_kamma.handlers = [handler]
logger_kamma.setLevel(logging.DEBUG)
logger_fqueue = logging.getLogger('kamma.queue')
logger_fqueue.handlers = [handler]
logger_fqueue.setLevel(logging.DEBUG)
logger = logging.getLogger('example')
logger.handlers = [handler]
logger.setLevel(logging.DEBUG)


# task callback
def task_fib(data):
    def fibonacci(n):
        if n < 0:
            raise Exception("Value must be >= 0")
        if n <= 1:
            return 1
        return fibonacci(n - 1) + fibonacci(n - 2)
    try:
        n = data['n']
        print("computing fibonacci({})".format(n))
        result = fibonacci(n)
        print("*** fibonacci({}): {} ***".format(n, result))
    except Exception as e:
        raise kamma.AbortTask(str(e))


if __name__ == "__main__":
    # kamma worker, we define the TaskCallback
    worker = KammaWorker(queue_path="task_queue",
                         task_callbacks=[kamma.TaskCallback(id='fibonacci', callback=task_fib)])
    # start listening for incoming tasks
    worker.run_async()
    print("ctrl+c to exit")
    try:
        while True:
            n = int(input("Fibonacci of: "))
            # add new fibonacci task
            worker.push_task(kamma.Task(id='fibonacci', data={'n': n}))
    except KeyboardInterrupt:
        pass
    worker.wait_empty_event()
    worker.stop()
    print("bye")
