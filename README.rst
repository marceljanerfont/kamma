kamma
=====
**kamma** is a very simplified task file queue that persists tasks and its needed data. It also has a worker that process all pending tasks.

|Version| |Versions| |Status| |Coverage| |License|

Motivation
----------
Nowadays local disk access is an undervalued resource for many reasons, however stored data is always available even after power outage. By contrast, network resources or remote third parties are not always ready. Is for this reason I developed the **kamma** in order to isolate *dependent* tasks from the miseries of remote services. **kamma** would try process all pending tasks forever respecting the queue order.

Limitations
-----------
* Up to ``(sys.maxint - FileQue.max_head_index)`` tasks can be queued as maximum.
* **All task's arguments should be serializable by json**
* Not recommended for high performance scenarios.

Install
-------
As simple as: 

    ``pip install kamma``


Example
-------

.. code-block:: python

    import kamma

    # python 2 and 3 compatibility issue
    try:
       input = raw_input
    except NameError:
       pass

    # kamma worker
    app = kamma.Worker()

    # registering fibonacci callback in kamma app
    @app.task_callback(timeout=5, retry_wait=task.wait_fixed(1),
                       retry_stop=task.stop_after_attempt(1))
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

The complete example here: ``examples/example.py``


.. |Version| image:: https://img.shields.io/pypi/v/kamma.svg?
   :target: http://badge.fury.io/py/kamma

.. |Versions| image:: https://img.shields.io/pypi/pyversions/kamma.svg
    :target: https://pypi.python.org/pypi/kamma

.. |Status| image:: https://img.shields.io/travis/marceljanerfont/kamma.svg?
   :target: https://travis-ci.org/marceljanerfont/kamma

.. |Coverage| image:: https://img.shields.io/codecov/c/github/marceljanerfont/kamma.svg?
   :target: https://codecov.io/github/marceljanerfont/kamma?branch=production

.. |License| image:: https://img.shields.io/pypi/l/kamma.svg?
   target: https://pypi.python.org/pypi/kamma
