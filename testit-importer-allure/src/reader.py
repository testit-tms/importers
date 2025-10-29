from abc import ABCMeta, abstractmethod
from typing import BinaryIO


class Reader:
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_all_files(self):
        pass

    @abstractmethod
    def read_file(self, file_name: str):
        pass

    @abstractmethod
    def read_attachment(self, file_name: str) -> BinaryIO:
        pass

    @abstractmethod
    def remove_attachment(self, file_name: str):
        pass
