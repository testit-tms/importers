import os

from .status import Status
from .configurator import Configurator
from xml.dom import minidom

from .testcase import TestCase


class Parser:

    def __init__(self, config: Configurator):
        self.__path_to_results = config.get_path()

    def read_file(self):
        results = []
        files = self.__get_files()
        for file in files:
            file_name, file_extension = os.path.splitext(file)

            if file_extension != '.xml':
                continue

            xml = minidom.parse(self.__path_to_results + '/' + file)
            testcases = xml.getElementsByTagName('testcase')

            for elem in testcases:
                name = elem.attributes['name'].value
                class_name = self.__get_class_name(elem.attributes['classname'].value)
                name_space = self.__get_name_space(elem.attributes['classname'].value, class_name)
                duration = elem.attributes['time'].value

                testcase = TestCase(name, name_space, class_name, duration)

                if elem.childNodes is not None:
                    for child in elem.childNodes:
                        if child.nodeName == 'error' or child.nodeName == 'failure':
                            testcase.set_message(child.attributes['message'].value)
                            testcase.set_trace(child.firstChild.nodeValue)
                            testcase.set_status(Status.FAILED)
                        elif child.nodeName == 'skipped':
                            testcase.set_message(child.attributes['message'].value)
                            testcase.set_status(Status.FAILED)

                results.append(testcase)

        return results

    def __get_files(self):
        files = []
        if os.path.isdir(self.__path_to_results):
            self.__path_to_results = os.path.abspath(self.__path_to_results)

            if self.__path_to_results[-1] != '/':
                self.__path_to_results += '/'

            return os.listdir(self.__path_to_results)

        if os.path.isfile(self.__path_to_results):
            files.append(os.path.basename(self.__path_to_results))
            self.__path_to_results = os.path.dirname(os.path.abspath(self.__path_to_results))

        return files

    @staticmethod
    def __get_class_name(value: str):
        parts = value.split('.')
        return parts[len(parts) - 1]

    @staticmethod
    def __get_name_space(value: str, delimiter: str):
        parts = value.split(delimiter)
        return parts[0][:-1]
