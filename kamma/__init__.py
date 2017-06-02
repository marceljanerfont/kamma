# -*- encoding: utf-8 -*-

__version__ = '0.0.2'

import logging
try:
    # not available in python 2.6
    from logging import NullHandler
except ImportError:

    class NullHandler(logging.Handler):

        def emit(self, record):
            pass

# Add NullHandler to prevent logging warnings
logging.getLogger(__name__).addHandler(NullHandler())


class TaskNotRegistered(Exception):
    pass
