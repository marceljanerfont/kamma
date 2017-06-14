# -*- coding: utf-8 -*-
import os
import glob
import logging
import threading
import traceback
from multiprocessing import Manager

logger = logging.getLogger(__name__)


class FileQueue:
    def __init__(self, path, max_head_index=100):
        self._path = path
        self._max_head_index = max_head_index
        # self._manager = Manager()
        self._items = list()  #  self._manager.list()
        self._mutex = threading.Lock()
        with self._mutex:
            logger.info("initializing FileQueue at {}".format(self._path))
            if not os.path.isdir(self._path):
                os.makedirs(self._path)
            self.__load_items()

    def length(self):
        with self._mutex:
            return len(self._items)

    def head(self):
        with self._mutex:
            head_idx = self.__head_index
            if head_idx >= 0:
                logger.debug("head item: {}/{}".format(head_idx, len(self._items)))
                with open(self.__filename(head_idx), "r") as file:
                    return file.read()
            return None

    def pop(self):
        with self._mutex:
            text = None
            head_idx = self.__head_index
            if head_idx >= 0:
                logger.debug("pop item: {}/{}".format(head_idx, len(self._items)))
                with open(self.__filename(head_idx), "r") as file:
                    text = file.read()
                os.remove(self.__filename(head_idx))
                self._items.pop(0)
                # rotate items
                if self._max_head_index >= 0 and self.__head_index == self._max_head_index:
                    self.__rotate_items()
                # logger.debug("after pop items: {}".format(self._items))
            return text

    def push(self, text):
        self._mutex.acquire()
        try:
            item = self.__tail_index + 1
            logger.debug("push item: {}/{}".format(item, len(self._items)))
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
        with self._mutex:
            return self.__head_index

    @property
    def max_head_index(self):
        return self._max_head_index

    @property
    def tail_index(self):
        with self._mutex:
            return self.__tail_index

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
