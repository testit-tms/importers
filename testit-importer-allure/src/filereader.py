"""The module provides functionality for reading result files from file system"""
import logging
import os
from interface import implements

from .filedto import FileDto
from .reader import Reader


class FileReader(implements(Reader)):
    """Class representing a reader"""

    def __init__(self, path_to_results: str):
        self.__path_to_results = path_to_results

    def get_all_files(self):
        """Function returns all result files."""
        files = []
        if os.path.isdir(self.__path_to_results):
            self.__path_to_results = os.path.abspath(self.__path_to_results)

            if self.__path_to_results[-1] != '/':
                self.__path_to_results += '/'

            files = [f for f in os.listdir(self.__path_to_results) if
                     os.path.isfile(os.path.join(self.__path_to_results, f))]

            return files

        if os.path.isfile(self.__path_to_results):
            files.append(os.path.basename(self.__path_to_results))
            self.__path_to_results = os.path.dirname(os.path.abspath(self.__path_to_results))

        return files

    def read_file(self, file_name: str):
        """Function reads result file by name."""
        return FileDto(file_name, open(f"{self.__path_to_results}{file_name}", encoding='UTF-8'))

    def read_attachment(self, file_name: str):
        """Function reads attachment by name."""
        if os.path.exists(f"{self.__path_to_results}{file_name}"):
            return open(f"{self.__path_to_results}{file_name}", 'rb')

        logging.error(f"Can't read attachment: {self.__path_to_results}{file_name} does not exist!")

    def remove_attachment(self, file_name: str):
        """Function removes attachment by name."""
        return
