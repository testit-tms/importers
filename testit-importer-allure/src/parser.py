"""The module provides functionality for parsing result files"""
import os
import json
import hashlib
import xmltodict
from .filedto import FileDto
from .reader import Reader


class Parser:
    """Class representing a parser"""

    def __init__(self, reader: Reader):
        self.__reader = reader
        self.__data_tests = {}
        self.__data_fixtures = {}

    def parse_results(self):
        """Function parses results"""
        files = self.__reader.get_all_files()

        for file in files:
            self.__read(file)

        return self.__data_tests, self.__data_fixtures

    def parse_attachment(self, file_name: str):
        """Function parses attachment"""
        return self.__reader.read_attachment(file_name)

    def clean_attachment(self, file_name: str):
        """Function cleans after attachment"""
        self.__reader.remove_attachment(file_name)

    def __read(self, file_path: str):
        file_name, file_extension = os.path.splitext(file_path)
        file: FileDto = self.__reader.read_file(file_path)

        if file_extension == '.json':
            self.__read_json(file)
        elif file_extension == '.xml' and file_name[-9:] == 'testsuite':
            self.__read_xml(file)

    def __read_json(self, file_dto: FileDto):
        result_data = json.load(file_dto.file)

        if 'result' in file_dto.name:
            if 'historyId' not in result_data:
                result_data['historyId'] = self.__get_hash(result_data['fullName'])

            if result_data['historyId'] not in self.__data_tests or \
                    result_data['start'] > self.__data_tests[result_data['historyId']]['start']:
                self.__data_tests[str(result_data['historyId'])] = result_data

        elif 'container' in file_dto.name:
            if 'children' in result_data:
                self.__data_fixtures[result_data['uuid']] = result_data

    def __read_xml(self, file_dto: FileDto):
        testsuite = xmltodict.parse(file_dto.file.read())
        testcases_data = testsuite['ns2:test-suite']['test-cases']['test-case']

        if isinstance(testcases_data, list):
            for testcase in testcases_data:
                self.__read_xml_testcase(testcase)
        else:
            self.__read_xml_testcase(testcases_data)

    def __read_xml_testcase(self, testcase: dict):
        if testcase['title'] and testcase['name']:
            md5 = hashlib.md5()
            md5.update(testcase['title'].encode('utf-8'))
            testcase_id = md5.hexdigest()

            if testcase_id not in self.__data_tests \
                    or testcase['@start'] > self.__data_tests[testcase_id]['@start']:
                self.__data_tests[testcase_id] = testcase

    @staticmethod
    def __get_hash(value: str):
        md = hashlib.sha256(bytes(value, encoding='utf-8'))
        return md.hexdigest()
