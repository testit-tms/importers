"""The module provides functionality for parsing result files"""
import os
import json
import hashlib
import xmltodict
from .filedto import FileDto
from .reader import Reader


# TODO: implement JSON and XML parsing using models as in migrators
class Parser:
    """Class representing a parser"""

    def __init__(self, reader: Reader):
        self.__reader = reader
        self.__data_tests = {}
        self.__data_containers = {}

    def parse_results(self):
        """Function parses results"""
        files = self.__reader.get_all_files()

        for file in files:
            self.__read(file)

        return self.__data_tests, self.__data_containers

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
        content = file_dto.file.read()

        if not content:
            return

        result_data = json.loads(content)

        if 'result' in file_dto.name:
            if 'historyId' not in result_data:
                if 'fullName' in result_data:
                    result_data['historyId'] = self.__get_hash(result_data['fullName'])
                else:
                    result_data['historyId'] = self.__get_hash(result_data['uuid'])

            if str(result_data['historyId']) not in self.__data_tests:
                self.__data_tests[str(result_data['historyId'])] = []

            self.__data_tests[str(result_data['historyId'])].append(result_data)

        elif 'container' in file_dto.name:
            if 'children' in result_data:
                self.__data_containers[result_data['uuid']] = result_data

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

            if testcase_id not in self.__data_tests:
                self.__data_tests[testcase_id] = []

            self.__data_tests[testcase_id].append(testcase)

    @staticmethod
    def __get_hash(value: str):
        md = hashlib.sha256(bytes(value, encoding='utf-8'))
        return md.hexdigest()
