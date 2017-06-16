
# -*- encoding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import kamma

# import logging

# handler = logging.StreamHandler()
# handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)-8s] [%(name)-10s] [%(lineno)-4d] %(message)s'))
# logger_kamma = logging.getLogger('kamma.app')
# logger_kamma.handlers = [handler]
# logger_kamma.setLevel(logging.DEBUG)
# logger_fqueue = logging.getLogger('kamma.queue')
# logger_fqueue.handlers = [handler]
# # logger_fqueue.setLevel(logging.DEBUG)
# logger = logging.getLogger('example')
# logger.handlers = [handler]
# logger.setLevel(logging.DEBUG)

try:
   input = raw_input
except NameError:
   pass

# kamma worker
app = kamma.Worker()


# registering on_failure callback that will be called after task error
@app.on_failure()
def on_failure(json_task, retry_stopped):
    print("--- FAILURE: attempts: {}, error: {} ---".format(retry_stopped.attempts,
                                                            retry_stopped.last_error))


# registering on_abort callback. It will be called each time that kamma.AbortTask is raised
@app.on_abortion()
def on_abortion(json_task, reason):
    print("--- ABORTION: {} ---".format(reason))


# registering fibonacci callback in kamma app
@app.task_callback(timeout=5, retry_wait=kamma.wait_fixed(1),
                   retry_stop=kamma.stop_after_attempt(1))
def fibonacci(n, level=0):
    result = 1
    if n < 0 or n > 100:
        raise kamma.AbortTask("n has to be 0 <= n <= 100")
    if n > 1:
        result = fibonacci(n - 1, level=level + 1) + fibonacci(n - 2, level=level + 1)
    if level == 0:
        print("*** RESULT: fibonacci of '{}' is '{}' ***".format(n, result))
    return result


if __name__ == "__main__":
    # start listening for incoming tasks
    app.run_async()
    print("Enter the value of the fibonacci you want to compute, 0 to exit")
    n = 1
    while True:
        n = int(input(""))
        if n == 0:
            break
        # add new fibonacci task
        app.push_task(fibonacci, n=n)
    app.stop()
    print("bye")
