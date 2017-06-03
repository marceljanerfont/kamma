kamma
=====
**kamma** is a very simplified task file queue that persists tasks and its needed data. It also has a worker that process all pending tasks.

|Version| |Status| |Coverage| |License|

Motivation
----------
Nowadays local disk access is an undervalued resource for many reasons, however stored data is always available even after power outage. By contrast, network resources or remote third parties are not always ready. Is for this reason I developed the **kamma** in order to isolate *dependent* tasks from the miseries of remote services. **kamma** would try process all pending tasks forever respecting the queue order.

Limitations
-----------
Up to ``(sys.maxint - FileQue.max_head_index)`` items can hold the queue. Not recommended for high performance scenarios.

Install
-------
As simple as: 


    pip install kamma


Example
-------

.. code-block:: python

    import kamma
    from kamma.worker import KammaWorker

    try:
       input = raw_input
    except NameError:
       pass

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



.. |Version| image:: https://img.shields.io/pypi/v/kamma.svg?
   :target: http://badge.fury.io/py/kamma

.. |Status| image:: https://img.shields.io/travis/marceljanerfont/kamma.svg?
   :target: https://travis-ci.org/marceljanerfont/kamma

.. |Coverage| image:: https://img.shields.io/codecov/c/github/marceljanerfont/kamma.svg?
   :target: https://codecov.io/github/marceljanerfont/kamma?branch=production

.. |License| image:: https://img.shields.io/pypi/l/kamma.svg?
   target: https://pypi.python.org/pypi/kamma
