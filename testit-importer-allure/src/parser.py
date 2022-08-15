"""The module provides functionality for parsing result files"""
from typing import TextIO

from .reader import Reader
import os
import json
import hashlib
import xmltodict


class Parser:
    """Class representing a parser"""

    def __init__(self, reader: Reader):
        self.__reader = reader
        self.__data_tests = {}
        self.__data_fixtures = {}

    def parse_results(self):
        files = self.__reader.get_all_files()

        for file in files:
            self.__read(file)

        return self.__data_tests, self.__data_fixtures

    def parse_attachment(self, file_name):
        return self.__reader.read_attachment(file_name)

    def __read(self, file_path: str):
        file_name, file_extension = os.path.splitext(file_path)
        file: TextIO = self.__reader.read_file(file_path)

        if file_extension == '.json':
            self.__read_json(file)
        elif file_extension == '.xml' and file_name[-9:] == 'testsuite':
            self.__read_xml(file)

    def __read_json(self, file: TextIO):
        result_data = json.load(file)

        if 'result' in file.name:
            if result_data['historyId'] not in self.__data_tests \
                    or result_data['start'] > self.__data_tests[result_data['historyId']]['start']:
                self.__data_tests[result_data['historyId']] = result_data

        elif 'container' in file.name:
            if 'children' in result_data:
                self.__data_fixtures[result_data['uuid']] = result_data

    def __read_xml(self, file: TextIO):
        testsuite = xmltodict.parse(file.read())

        for testcase in testsuite['ns2:test-suite']['test-cases']['test-case']:
            if testcase['title'] and testcase['name']:
                md5 = hashlib.md5()
                md5.update(testcase['title'].encode('utf-8'))
                testcase_id = md5.hexdigest()

                if testcase_id not in self.__data_tests \
                        or testcase['@start'] > self.__data_tests[testcase_id]['@start']:
                    self.__data_tests[testcase_id] = testcase
