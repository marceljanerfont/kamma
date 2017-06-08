
# -*- encoding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import kamma
from kamma.app import Kamma
import logging

try:
   input = raw_input
except NameError:
   pass

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)-8s] [%(name)-10s] [%(lineno)-4d] %(message)s'))
logger_kamma = logging.getLogger('kamma.app')
logger_kamma.handlers = [handler]
logger_kamma.setLevel(logging.DEBUG)
logger_fqueue = logging.getLogger('kamma.queue')
logger_fqueue.handlers = [handler]
logger_fqueue.setLevel(logging.DEBUG)
logger = logging.getLogger('example')
logger.handlers = [handler]
logger.setLevel(logging.DEBUG)

# kamma worker
app = Kamma()


# task callback
# todo: https://julien.danjou.info/blog/2015/python-retrying
@app.task('fibonacci')
def task_fib(data):
    def fibonacci(n):
        if n < 0 or n > 42:
            raise Exception("n has to be 0 <= n <= 42")
        if n <= 1:
            return 1
        return fibonacci(n - 1) + fibonacci(n - 2)
    try:
        n = data['n']
        result = fibonacci(n)
        print("*** fibonacci({}): {} ***".format(n, result))
    except Exception as e:
        # abort task when an exception occurs
        raise kamma.AbortTask(str(e))


if __name__ == "__main__":
    # start listening for incoming tasks
    app.run_async()
    print("ctrl+c to exit")
    try:
        while True:
            n = int(input("Fibonacci of: "))
            # add new fibonacci task
            app.push_task(kamma.Task('fibonacci', data={'n': n}))
    except KeyboardInterrupt:
        pass
    app.stop()
    print("bye")
