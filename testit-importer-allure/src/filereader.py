"""The module provides functionality for reading result files"""
import os
import json
import hashlib
import xmltodict
from interface import implements
from .reader import Reader


class FileReader(implements(Reader)):
    """Class representing a reader"""

    def __init__(self, path_to_results: str):
        self.__path_to_results = path_to_results
        self.__data_tests = {}
        self.__data_fixtures = {}

    def read_result_files(self):
        """Function returns tests and fixtures from result files."""
        if os.path.isdir(self.__path_to_results):
            self.__path_to_results = os.path.abspath(self.__path_to_results)

            if self.__path_to_results[-1] != '/':
                self.__path_to_results += '/'

            full_names = os.listdir(self.__path_to_results)

            for full_name in full_names:
                file_name, file_extension = os.path.splitext(full_name)
                file_path = self.__path_to_results + full_name

                self.__read(file_path, file_name, file_extension)

        elif os.path.isfile(self.__path_to_results):
            self.__path_to_results = os.path.dirname(os.path.abspath(self.__path_to_results))
            file_name, file_extension = os.path.splitext(self.__path_to_results)
            file_path = self.__path_to_results

            self.__read(file_path, file_name, file_extension)

        return self.__data_tests, self.__data_fixtures

    def read_attachment(self, name: str):
        return open(f"{self.__path_to_results}{name}", 'rb')

    def __read(self, file_path: str, file_name: str, file_extension: str):
        if file_extension == '.json':
            self.__read_json(file_path, file_name)
        elif file_extension == '.xml' and file_name[-9:] == 'testsuite':
            self.__read_xml(file_path)

    def __read_json(self, file_path: str, file_name: str):
        with open(file_path, encoding='UTF-8') as file:
            result_data = json.load(file)

        if file_name[-6:] == 'result':
            if result_data['historyId'] not in self.__data_tests \
                    or result_data['start'] > self.__data_tests[result_data['historyId']]['start']:
                self.__data_tests[result_data['historyId']] = result_data

        elif file_name[-9:] == 'container':
            if 'children' in result_data:
                self.__data_fixtures[result_data['uuid']] = result_data

    def __read_xml(self, file_path: str):
        with open(file_path, encoding='UTF-8') as file:
            testsuite = xmltodict.parse(file.read())

        for testcase in testsuite['ns2:test-suite']['test-cases']['test-case']:
            if testcase['title'] and testcase['name']:
                md5 = hashlib.md5()
                md5.update(testcase['title'].encode('utf-8'))
                testcase_id = md5.hexdigest()

                if testcase_id not in self.__data_tests \
                        or testcase['@start'] > self.__data_tests[testcase_id]['@start']:
                    self.__data_tests[testcase_id] = testcase
