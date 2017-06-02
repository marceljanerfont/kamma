# -*- coding: utf-8 -*-
import os
import glob
import logging
import threading
import traceback
from multiprocessing import Manager

logger = logging.getLogger(__name__)


class FileQueue:
    def __init__(self, path, max_head_index=10):
        self._path = path
        self._max_head_index = max_head_index
        self._manager = Manager()
        self._items = self._manager.list()
        self._mutex = threading.Lock()
        self._mutex.acquire()
        try:
            logger.info("initializing FileQueue at {}".format(self._path))
            if not os.path.isdir(self._path):
                os.makedirs(self._path)
            self.__load_items()
        finally:
            self._mutex.release()

    def purgue(self):
        logger.info("purgue queue")
        self._mutex.acquire()
        try:
            for item in self._items:
                os.remove(self.__filename(item))
            del self._items[:]
        finally:
            self._mutex.release()

    def length(self):
        self._mutex.acquire()
        try:
            return len(self._items)
        finally:
            self._mutex.release()

    def head(self):
        self._mutex.acquire()
        try:
            head_idx = self.__head_index
            if head_idx >= 0:
                logger.debug("head item: {}".format(head_idx))
                with open(self.__filename(head_idx), "r") as file:
                    return file.read()
            return None
        finally:
            self._mutex.release()

    def pop(self):
        self._mutex.acquire()
        try:
            text = None
            head_idx = self.__head_index
            if head_idx >= 0:
                logger.debug("pop item: {}".format(head_idx))
                with open(self.__filename(head_idx), "r") as file:
                    text = file.read()
                os.remove(self.__filename(head_idx))
                self._items.pop(0)
                # rotate items
                if self._max_head_index >= 0 and self.__head_index == self._max_head_index:
                    self.__rotate_items()
                # logger.debug("after pop items: {}".format(self._items))
            return text
        finally:
            self._mutex.release()

    def push(self, text):
        self._mutex.acquire()
        try:
            item = self.__tail_index + 1
            logger.debug("push item: {}".format(item))
            with open(self.__filename(item), "w") as file:
                file.write(text)
            self._items.append(item)
        except Exception:
            logger.error(traceback.format_exc())
            raise Exception("cannot push item")
        finally:
            self._mutex.release()

    @property
    def head_index(self):
        self._mutex.acquire()
        try:
            return self.__head_index
        finally:
            self._mutex.release()

    @property
    def max_head_index(self):
        return self._max_head_index

    @property
    def tail_index(self):
        self._mutex.acquire()
        try:
            return self.__tail_index
        finally:
            self._mutex.release()

    @property
    def __head_index(self):
        return self._items[0] if len(self._items) > 0 else -1

    @property
    def __tail_index(self):
        return self._items[len(self._items) - 1] if len(self._items) > 0 else -1

    def __load_items(self):
        self._items = [int(os.path.basename(file)[:-5]) for file in glob.glob(self._path + "/*.json")]
        self._items.sort()
        logger.debug("loaded items: {}".format(self._items))

    def __filename(self, item):
        return self._path + "/" + str(item) + ".json"

    def __rotate_items(self):
        logger.debug("rotating queue items: {}".format(self._items))
        counter = 0
        for item in self._items:
            # logger.debug("moving {} -> {}".format(self.__filename(item), self.__filename(counter)))
            os.rename(self.__filename(item), self.__filename(counter))
            counter = counter + 1
        self.__load_items()