# kamma
**kamma** is a very simplified task file queue that persist jobs and its argument data. Also it has a worker that process all pending jobs.

|Version| |Status| |Coverage| |License|

## Motivation
Nowadays local disk access is undervalued resource because it is slow, is local and maybe is too trivial, however stored data is always available even after power outage. By contrast, network resources or remote third parties are not always ready to use. It is for these reason that I developed **kamma** to isolate *dependent* tasks from the miseries of the remote services. **kamma** would try to process forever always respecting the FIFO order.

## Limitation
Up to 100k items queue

## Install

'''
    pip install kamma
'''


.. |Version| image:: https://img.shields.io/pypi/v/kamma.svg?
   :target: http://badge.fury.io/py/kamma

.. |Status| image:: https://img.shields.io/travis/marceljanerfont/kamma.svg?
   :target: https://travis-ci.org/marceljanerfont/kamma

.. |Coverage| image:: https://img.shields.io/codecov/c/github/marceljanerfont/kamma.svg?
   :target: https://codecov.io/github/marceljanerfont/kamma?branch=production

.. |License| image:: https://img.shields.io/pypi/l/kamma.svg?
   target: https://pypi.python.org/pypi/kamma
