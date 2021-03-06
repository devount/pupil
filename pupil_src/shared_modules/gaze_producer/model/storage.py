"""
(*)~---------------------------------------------------------------------------
Pupil - eye tracking platform
Copyright (C) 2012-2019 Pupil Labs

Distributed under the terms of the GNU
Lesser General Public License (LGPL v3.0).
See COPYING and COPYING.LESSER for license details.
---------------------------------------------------------------------------~(*)
"""
import abc
import logging
import os
import random
import re

import file_methods as fm

logger = logging.getLogger(__name__)


class StorageItem(abc.ABC):
    @property
    @abc.abstractmethod
    def version(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def from_tuple(tuple_):
        pass

    @property
    @abc.abstractmethod
    def as_tuple(self):
        pass

    @staticmethod
    def create_new_unique_id():
        """
        Returns: A string like e.g. "04bfd332"
        """
        return "{:0>8x}".format(random.getrandbits(32))

    @staticmethod
    def create_unique_id_from_string(string):
        """
        Returns: A unique id as generated by create_new_unique_id(), but for
            the same input string, it will always return the same id.
        """
        old_state_of_random = random.getstate()
        random.seed(string)
        unique_id = StorageItem.create_new_unique_id()
        random.setstate(old_state_of_random)
        return unique_id



class Storage(abc.ABC):
    def __init__(self, plugin):
        plugin.add_observer("cleanup", self._on_cleanup)

    def __iter__(self):
        return iter(self.items)

    @abc.abstractmethod
    def add(self, item):
        pass

    @abc.abstractmethod
    def delete(self, item):
        pass

    @property
    @abc.abstractmethod
    def items(self):
        pass

    @property
    @abc.abstractmethod
    def _item_class(self):
        pass

    @abc.abstractmethod
    def save_to_disk(self):
        pass

    @abc.abstractmethod
    def _load_from_disk(self):
        pass

    def _save_data_to_file(self, filepath, data):
        dict_representation = {"version": self._item_class.version, "data": data}
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        fm.save_object(dict_representation, filepath)

    def _load_data_from_file(self, filepath):
        try:
            dict_representation = fm.load_object(filepath)
        except FileNotFoundError:
            return None
        if dict_representation.get("version", None) != self._item_class.version:
            logger.warning(
                "Data in {} is in old file format. Will not load these!".format(
                    filepath
                )
            )
            return None
        return dict_representation.get("data", None)

    def _on_cleanup(self):
        self.save_to_disk()

    @staticmethod
    def get_valid_filename(file_name):
        """
        Return the given string converted to a string that can be used for a clean
        filename. Remove leading and trailing spaces; convert other spaces to
        underscores; and remove anything that is not an alphanumeric, dash,
        underscore, or dot.
        E.g.: get_valid_filename("john's portrait in 2004.jpg")
        'johns_portrait_in_2004.jpg'

        Copied from Django:
        https://github.com/django/django/blob/master/django/utils/text.py#L219
        """
        file_name = str(file_name).strip().replace(' ', '_')
        # django uses \w instead of _a-zA-Z0-9 but this leaves characters like ä, Ü, é
        # in the filename, which might be problematic
        return re.sub(r'(?u)[^-_a-zA-Z0-9.]', '', file_name)
