kamma
=====
**kamma** is a very simplified task file queue that persists tasks and its needed data. It also has a worker that process all pending tasks.

|Version| |Status| |Coverage| |License|

Motivation
----------
Nowadays local disk access is undervalued resource for many reasons, however stored data is always available even after power outage. By contrast, network resources or remote third parties are not always ready to use. For this reason I developed **kamma** in order to isolate *dependent* tasks from the miseries of remote services. **kamma** would try process all pending tasks forever respecting the queue order.

Limitations
-----------
Up to ``(sys.maxint - FileQue.max_head_index)`` items can hold the queue. Not recommended for high performance scenarios.

Install
-------
As simple as: 


    pip install kamma


.. |Version| image:: https://img.shields.io/pypi/v/kamma.svg?
   :target: http://badge.fury.io/py/kamma

.. |Status| image:: https://img.shields.io/travis/marceljanerfont/kamma.svg?
   :target: https://travis-ci.org/marceljanerfont/kamma

.. |Coverage| image:: https://img.shields.io/codecov/c/github/marceljanerfont/kamma.svg?
   :target: https://codecov.io/github/marceljanerfont/kamma?branch=production

.. |License| image:: https://img.shields.io/pypi/l/kamma.svg?
   target: https://pypi.python.org/pypi/kamma
