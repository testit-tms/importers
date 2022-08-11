import os
import json
import xmltodict
import hashlib


class Reader:

    def __init__(self, path_to_results):
        self.path_to_results = path_to_results

    @staticmethod
    def read(file_path, file_name, file_extension, data_tests, data_before_after):
        if file_extension == '.json':
            if file_name[-6:] == 'result':
                result = json.load(open(file_path, encoding='UTF-8'))

                if result['historyId'] not in data_tests or result['start'] > data_tests[result['historyId']]['start']:
                    data_tests[result['historyId']] = result
            elif file_name[-9:] == 'container':
                container = json.load(open(file_path, encoding='UTF-8'))

                if 'children' in container:
                    data_before_after[container['uuid']] = container
        elif file_extension == '.xml' and file_name[-9:] == 'testsuite':
            testsuite = xmltodict.parse(open(file_path, encoding='UTF-8').read())

            for testcase in testsuite['ns2:test-suite']['test-cases']['test-case']:
                if testcase['title'] and testcase['name']:
                    md5 = hashlib.md5()
                    md5.update(testcase['title'].encode('utf-8'))
                    testcase_id = md5.hexdigest()

                    if testcase_id not in data_tests or testcase['@start'] > data_tests[testcase_id]['@start']:
                        data_tests[testcase_id] = testcase

        return data_tests, data_before_after

    def get_result(self):
        data_tests = {}
        data_before_after = {}

        if os.path.isdir(self.path_to_results):
            self.path_to_results = os.path.abspath(self.path_to_results)

            if self.path_to_results[-1] != '/':
                self.path_to_results += '/'

            full_names = os.listdir(self.path_to_results)

            for full_name in full_names:
                file_name, file_extension = os.path.splitext(full_name)
                file_path = self.path_to_results + full_name

                data_tests, data_before_after = self.read(file_path, file_name, file_extension, data_tests,
                                                          data_before_after)

        elif os.path.isfile(self.path_to_results):
            self.path_to_results = os.path.dirname(os.path.abspath(self.path_to_results))
            file_name, file_extension = os.path.splitext(self.path_to_results)
            file_path = self.path_to_results

            data_tests, data_before_after = self.read(file_path, file_name, file_extension, data_tests,
                                                      data_before_after)

        return data_tests, data_before_after
