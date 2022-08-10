import argparse
import configparser
import os
import re

CONFIG_SECTION = 'testit'
CONFIG_URL = 'url'
CONFIG_PRIVATE_TOKEN = 'privatetoken'
CONFIG_PROJECT_ID = 'projectID'
CONFIG_CONFIGURATION_ID = 'configurationID'
CONFIG_NAME = 'connection_config.ini'


class Configurator:
    path_to_results = None
    path_to_config = None
    specified_testrun = None

    def __init__(self):
        self.__set_config()
        self.__set_parser()
        self.__parse_args()

    def get_path(self):
        return self.path_to_results

    def get_url(self):
        return self.config.get(CONFIG_SECTION, CONFIG_URL)

    def get_private_token(self):
        return self.config.get(CONFIG_SECTION, CONFIG_PRIVATE_TOKEN)

    def get_project_id(self):
        return self.config.get(CONFIG_SECTION, CONFIG_PROJECT_ID)

    def get_configuration_id(self):
        return self.config.get(CONFIG_SECTION, CONFIG_CONFIGURATION_ID)

    def __set_config(self):
        self.config = configparser.RawConfigParser()
        self.path_to_config = os.path.join(os.path.dirname(__file__)[:os.path.dirname(__file__).rindex(os.sep)],
                                           CONFIG_NAME)

        self.config.read(self.path_to_config)

    def __set_parser(self):
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

    def __parse_args(self):
        args = self.parser.parse_args()
        if args.set_url:
            if not re.fullmatch(
                    r'^(?:(?:(?:https?|ftp):)?//)?(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25['
                    r'0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-zA-Z0-9\u00a1-\uffff]['
                    r'a-zA-Z0-9\u00a1-\uffff_-]{0,62})?[a-zA-Z0-9\u00a1-\uffff]\.)+(?:[a-zA-Z\u00a1-\uffff]{2,'
                    r'}\.?))(?::\d{2,5})?(?:[/?#]\S*)?$',
                    args.set_url):
                print('The wrong URL!')
                raise SystemExit

            self.config.set(CONFIG_SECTION, CONFIG_URL,
                            args.set_url if args.set_url[-1] != '/' else args.set_url[:-1])

        if args.set_privatetoken:
            self.config.set(CONFIG_SECTION, CONFIG_PRIVATE_TOKEN, args.set_privatetoken)

        if args.set_project:
            if not re.fullmatch(r'[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}',
                                args.set_project):
                print('The wrong project ID!')
                raise SystemExit

            self.config.set(CONFIG_SECTION, CONFIG_PROJECT_ID, args.set_project)

        if args.set_configuration:
            if not re.fullmatch(r'[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}',
                                args.set_configuration):
                print('The wrong configuration ID!')
                raise SystemExit

            self.config.set(CONFIG_SECTION, CONFIG_CONFIGURATION_ID, args.set_configuration)

        if args.set_testrun:
            if not re.fullmatch(r'[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}',
                                args.set_testrun):
                print('The wrong testrun ID!')
                raise SystemExit

            self.specified_testrun = args.set_testrun

        if args.alluredir:
            self.path_to_results = args.alluredir

        if args.show_settings:
            print(
                f"url: {self.config.get(CONFIG_SECTION, CONFIG_URL)}\nprivatetoken: {self.config.get(CONFIG_SECTION, CONFIG_PRIVATE_TOKEN)}\nprojectID: {self.config.get(CONFIG_SECTION, CONFIG_PROJECT_ID)}\nconfigurationID: {self.config.get(CONFIG_SECTION, CONFIG_CONFIGURATION_ID)}")

        if args.set_url or args.set_privatetoken or args.set_project or args.set_configuration:
            with open(self.path_to_config, "w") as config_file:
                self.config.write(config_file)
