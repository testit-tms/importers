import os
import json
import argparse
import configparser
import re
import xmltodict
import hashlib


class AttributeReader:
    path_to_results = None
    path_to_config = None
    specified_testrun = None

    def __init__(self):
        self.config = configparser.RawConfigParser()
        self.path_to_config = os.path.join(os.path.dirname(__file__)[:os.path.dirname(__file__).rindex(os.sep)], 'connection_config.ini')
        self.config.read(self.path_to_config)
        self.parser = argparse.ArgumentParser(description='Test IT importer', add_help=True)
        self.parser.add_argument(
            '-u',
            '--url',
            action="store",
            default=None,
            dest="set_url",
            metavar="https://demo.testit.software",
            help='Set location of the Test IT instance'
        )
        self.parser.add_argument(
            '-pt',
            '--privatetoken',
            action="store",
            dest="set_privatetoken",
            metavar="T2lKd2pLZGI4WHRhaVZUejNl",
            help='Set API secret key'
        )
        self.parser.add_argument(
            '-pi',
            '--projectid',
            action="store",
            dest="set_project",
            metavar="5236eb3f-7c05-46f9-a609-dc0278896464",
            help='Set project ID'
        )
        self.parser.add_argument(
            '-ci',
            '--configurationid',
            action="store",
            dest="set_configuration",
            metavar="15dbb164-c1aa-4cbf-830c-8c01ae14f4fb",
            help='Set configuration ID'
        )
        self.parser.add_argument(
            '-ti',
            '--testrunid',
            action="store",
            dest="set_testrun",
            metavar="3802f329-190c-4617-8bb0-2c3696abeb8f",
            help='Set test run ID'
        )
        self.parser.add_argument(
            '-sh',
            '--show',
            action='store_true',
            dest="show_settings",
            help='Show the connection_config.ini file'
        )
        self.parser.add_argument(
            '-rd',
            '--resultsdir',
            action="store",
            dest="alluredir",
            metavar="DIR",
            default=None,
            help='Import the Allure report in the specified directory if it exists'
        )


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


    def get_attr(self):
        args = self.parser.parse_args()
        data_tests = {}
        data_before_after = {}

        if args.set_url:
            if not re.fullmatch(r'^(?:(?:(?:https?|ftp):)?//)?(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-zA-Z0-9\u00a1-\uffff][a-zA-Z0-9\u00a1-\uffff_-]{0,62})?[a-zA-Z0-9\u00a1-\uffff]\.)+(?:[a-zA-Z\u00a1-\uffff]{2,}\.?))(?::\d{2,5})?(?:[/?#]\S*)?$', args.set_url):
                print('The wrong URL!')
                raise SystemExit

            self.config.set('testit', 'url', args.set_url if args.set_url[-1] != '/' else args.set_url[:-1])

        if args.set_privatetoken:
            self.config.set('testit', 'privatetoken', args.set_privatetoken)

        if args.set_project:
            if not re.fullmatch(r'[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}', args.set_project):
                print('The wrong project ID!')
                raise SystemExit

            self.config.set('testit', 'projectID', args.set_project)

        if args.set_configuration:
            if not re.fullmatch(r'[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}', args.set_configuration):
                print('The wrong configuration ID!')
                raise SystemExit

            self.config.set('testit', 'configurationID', args.set_configuration)

        if args.set_testrun:
            if not re.fullmatch(r'[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}', args.set_testrun):
                print('The wrong testrun ID!')
                raise SystemExit

            self.specified_testrun = args.set_testrun

        if args.show_settings:
            print(f"url: {self.config.get('testit', 'url')}\nprivatetoken: {self.config.get('testit', 'privatetoken')}\nprojectID: {self.config.get('testit', 'projectID')}\nconfigurationID: {self.config.get('testit', 'configurationID')}")

        if args.alluredir:
            if os.path.isdir(args.alluredir):
                self.path_to_results = os.path.abspath(args.alluredir)

                if args.alluredir[-1] != '/':
                    args.alluredir += '/'

                full_names = os.listdir(args.alluredir)

                for full_name in full_names:
                    file_name, file_extension = os.path.splitext(full_name)
                    file_path = args.alluredir + full_name

                    data_tests, data_before_after = self.read(file_path, file_name, file_extension, data_tests, data_before_after)

            elif os.path.isfile(args.alluredir):
                self.path_to_results = os.path.dirname(os.path.abspath(args.alluredir))
                file_name, file_extension = os.path.splitext(args.alluredir)
                file_path = args.alluredir

                data_tests, data_before_after = self.read(file_path, file_name, file_extension, data_tests, data_before_after)

        if args.set_url or args.set_privatetoken or args.set_project or args.set_configuration:
            with open(self.path_to_config, "w") as config_file:
                self.config.write(config_file)

        return data_tests, data_before_after


    def get_path(self):
        return self.path_to_results


    def get_url(self):
        return self.config.get('testit', 'url')


    def get_privatetoken(self):
        return self.config.get('testit', 'privatetoken')


    def get_project_id(self):
        return self.config.get('testit', 'projectID')


    def get_configuration_id(self):
        return self.config.get('testit', 'configurationID')
