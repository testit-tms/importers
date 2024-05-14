"""The module provides functionality for working with the config"""
import argparse
import configparser
import os
import re

CONFIG_SECTION = 'testit'
CONFIG_URL = 'url'
CONFIG_PRIVATE_TOKEN = 'privateToken'
CONFIG_PROJECT_ID = 'projectID'
CONFIG_CONFIGURATION_ID = 'configurationID'
CONFIG_CERT_VALIDATION = 'certValidation'
CONFIG_NAME = 'connection_config.ini'
ALLURE_IGNORE_PACKAGE_NAME = 'ignorePackageName'

RABBITMQ_CONFIG_SECTION = 'rabbitmq'
RABBITMQ_CONFIG_URL = 'host'
RABBITMQ_CONFIG_USER = 'user'
RABBITMQ_CONFIG_PASSWORD = 'password'
RABBITMQ_CONFIG_EXCHANGE = 'exchange'

MINIO_CONFIG_SECTION = 'minio'
MINIO_CONFIG_URL = 'host'
MINIO_CONFIG_ACCESS_KEY = 'accessKey'
MINIO_CONFIG_SECRET_KEY = 'secretKey'



class Configurator:
    """Class representing a configurator"""

    path_to_results = None
    path_to_config = None
    specified_testrun = None
    specified_testrun_name = None

    def __init__(self):
        self.__set_config()
        self.__set_parser()
        self.__parse_args()
        self.__load_env_properties()

    def get_path(self):
        """Function returns path of result files."""
        return self.path_to_results

    def get_url(self):
        """Function returns TMS url."""
        return self.config.get(CONFIG_SECTION, CONFIG_URL)

    def get_private_token(self):
        """Function returns private token."""
        return self.config.get(CONFIG_SECTION, CONFIG_PRIVATE_TOKEN)

    def get_project_id(self):
        """Function returns project id."""
        return self.config.get(CONFIG_SECTION, CONFIG_PROJECT_ID)

    def get_configuration_id(self):
        """Function returns configuration id."""
        return self.config.get(CONFIG_SECTION, CONFIG_CONFIGURATION_ID)

    def get_cert_validation(self):
        """Function returns cert validation."""
        if not self.config.has_option(CONFIG_SECTION, CONFIG_CERT_VALIDATION):
            return

        return self.config.get(CONFIG_SECTION, CONFIG_CERT_VALIDATION)

    def get_ignore_package_name(self):
        """Function returns ignore package name."""
        return self.config.get(CONFIG_SECTION, ALLURE_IGNORE_PACKAGE_NAME)

    def get_rabbitmq_url(self):
        """Function returns rabbit mq url."""
        return self.config.get(RABBITMQ_CONFIG_SECTION, RABBITMQ_CONFIG_URL)

    def get_rabbitmq_user(self):
        """Function returns rabbit mq user."""
        return self.config.get(RABBITMQ_CONFIG_SECTION, RABBITMQ_CONFIG_USER)

    def get_rabbitmq_password(self):
        """Function returns rabbit mq user's password."""
        return self.config.get(RABBITMQ_CONFIG_SECTION, RABBITMQ_CONFIG_PASSWORD)

    def get_rabbitmq_exchange(self):
        """Function returns rabbit mq exchange."""
        return self.config.get(RABBITMQ_CONFIG_SECTION, RABBITMQ_CONFIG_EXCHANGE)

    def get_minio_url(self):
        """Function returns minio url."""
        return self.config.get(MINIO_CONFIG_SECTION, MINIO_CONFIG_URL)

    def get_minio_access_key(self):
        """Function returns minio access key."""
        return self.config.get(MINIO_CONFIG_SECTION, MINIO_CONFIG_ACCESS_KEY)

    def get_minio_secret_key(self):
        """Function returns minio secret key."""
        return self.config.get(MINIO_CONFIG_SECTION, MINIO_CONFIG_SECRET_KEY)

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
            '-tn',
            '--testrunname',
            action="store",
            dest="set_testrun_name",
            help='Set test run name'
        )
        self.parser.add_argument(
            '-cv',
            '--certvalidation',
            action="store",
            dest="set_cert_validation",
            metavar="false",
            help='Enables/disables certificate validation'
        )
        self.parser.add_argument(
            '-sh',
            '--show',
            action='store_true',
            dest="show_settings",
            help='Show the connection_config.ini file'
        )
        self.parser.add_argument(
            '-ipn',
            '--ignorepackagename',
            action="store",
            dest="ignore_package_name",
            metavar="True or False",
            default=False,
            help='Use parentSuite as namespace'
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
        self.parser.add_argument(
            '-rh',
            '--rabbitmqhost',
            action="store",
            dest="set_rabbitmqhost",
            metavar="localhost:5672",
            default=None,
            help='Host of Rabbit MQ'
        )
        self.parser.add_argument(
            '-ru',
            '--rabbitmquser',
            action="store",
            dest="set_rabbitmquser",
            metavar="user",
            default=None,
            help='User of Rabbit MQ'
        )
        self.parser.add_argument(
            '-rp',
            '--rabbitmqpassword',
            action="store",
            dest="set_rabbitmqpassword",
            metavar="password",
            default=None,
            help='Password of Rabbit MQ'
        )
        self.parser.add_argument(
            '-re',
            '--rabbitmqexchange',
            action="store",
            dest="set_rabbitmqexchange",
            metavar="exchange",
            default=None,
            help='Exchange of Rabbit MQ'
        )
        self.parser.add_argument(
            '-mh',
            '--miniohost',
            action="store",
            dest="set_miniohost",
            metavar="localhost:9000",
            default=None,
            help='Host of Minio'
        )
        self.parser.add_argument(
            '-mak',
            '--minioaccesskey',
            action="store",
            dest="set_minioaccesskey",
            metavar="accesskey",
            default=None,
            help='Access key of Minio'
        )
        self.parser.add_argument(
            '-msk',
            '--miniosecretkey',
            action="store",
            dest="set_miniosecretkey",
            metavar="secretkey",
            default=None,
            help='Secret key of Minio'
        )

    def __load_env_properties(self):
        if 'TMS_HOST' in os.environ.keys():
            self.config.set(CONFIG_SECTION, CONFIG_URL, os.environ.get('TMS_HOST'))

        if 'TMS_PRIVATE_TOKEN' in os.environ.keys():
            self.config.set(CONFIG_SECTION, CONFIG_PRIVATE_TOKEN, os.environ.get('TMS_PRIVATE_TOKEN'))

        if 'TMS_PROJECT_ID' in os.environ.keys():
            self.config.set(CONFIG_SECTION, CONFIG_PROJECT_ID, os.environ.get('TMS_PROJECT_ID'))

        if 'TMS_CONFIGURATION_ID' in os.environ.keys():
            self.config.set(CONFIG_SECTION, CONFIG_CONFIGURATION_ID, os.environ.get('TMS_CONFIGURATION_ID'))

        if f'TMS_CERT_VALIDATION' in os.environ.keys():
            self.config.set(CONFIG_SECTION, CONFIG_CERT_VALIDATION, os.environ.get('TMS_CERT_VALIDATION').lower())

        if 'MINIO_API_HOST' in os.environ.keys():
            self.config.set(MINIO_CONFIG_SECTION, MINIO_CONFIG_URL, os.environ.get('MINIO_API_HOST'))

        if 'MINIO_ACCESS_KEY' in os.environ.keys():
            self.config.set(MINIO_CONFIG_SECTION, MINIO_CONFIG_ACCESS_KEY, os.environ.get('MINIO_ACCESS_KEY'))

        if 'MINIO_SECRET_KEY' in os.environ.keys():
            self.config.set(MINIO_CONFIG_SECTION, MINIO_CONFIG_SECRET_KEY, os.environ.get('MINIO_SECRET_KEY'))

        if 'RABBITMQ_HOST' in os.environ.keys():
            self.config.set(RABBITMQ_CONFIG_SECTION, RABBITMQ_CONFIG_URL, os.environ.get('RABBITMQ_HOST'))

        if 'RABBITMQ_USER' in os.environ.keys():
            self.config.set(RABBITMQ_CONFIG_SECTION, RABBITMQ_CONFIG_USER, os.environ.get('RABBITMQ_USER'))

        if 'RABBITMQ_PASSWORD' in os.environ.keys():
            self.config.set(RABBITMQ_CONFIG_SECTION, RABBITMQ_CONFIG_PASSWORD, os.environ.get('RABBITMQ_PASSWORD'))

        if 'RABBITMQ_EXCHANGE' in os.environ.keys():
            self.config.set(RABBITMQ_CONFIG_SECTION, RABBITMQ_CONFIG_EXCHANGE, os.environ.get('RABBITMQ_EXCHANGE'))

    def __parse_args(self):
        args = self.parser.parse_args()
        if args.set_url:
            if not re.fullmatch(
                    r"^(ht|f)tp(s?)\:\/\/[0-9a-zA-Z]([-.\w]*[0-9a-zA-Z])*(:(0-9)*)*(\/?)([a-zA-Z0-9\-\.\?\,\'\/\\\+&amp;%\$#_]*)?$",
                    args.set_url):
                print('The wrong URL!')
                raise SystemExit

            self.config.set(CONFIG_SECTION, CONFIG_URL,
                            args.set_url if args.set_url[-1] != '/' else args.set_url[:-1])

        if args.set_privatetoken:
            self.config.set(CONFIG_SECTION, CONFIG_PRIVATE_TOKEN, args.set_privatetoken)

        if args.set_project:
            if not re.fullmatch(r"[a-zA-Z\d]{8}-[a-zA-Z\d]{4}-[a-zA-Z\d]{4}-[a-zA-Z\d]{4}-[a-zA-Z\d]{12}",
                                args.set_project):
                print('The wrong project ID!')
                raise SystemExit

            self.config.set(CONFIG_SECTION, CONFIG_PROJECT_ID, args.set_project)

        if args.set_configuration:
            if not re.fullmatch(r'[a-zA-Z\d]{8}-[a-zA-Z\d]{4}-[a-zA-Z\d]{4}-[a-zA-Z\d]{4}-[a-zA-Z\d]{12}',
                                args.set_configuration):
                print('The wrong configuration ID!')
                raise SystemExit

            self.config.set(CONFIG_SECTION, CONFIG_CONFIGURATION_ID, args.set_configuration)

        if args.set_testrun:
            if not re.fullmatch(r'[a-zA-Z\d]{8}-[a-zA-Z\d]{4}-[a-zA-Z\d]{4}-[a-zA-Z\d]{4}-[a-zA-Z\d]{12}',
                                args.set_testrun):
                print('The wrong testrun ID!')
                raise SystemExit

            self.specified_testrun = args.set_testrun

        if args.set_testrun_name:
            self.specified_testrun_name = args.set_testrun_name

        if args.set_cert_validation:
            self.config.set(CONFIG_SECTION, CONFIG_CERT_VALIDATION, args.set_cert_validation.lower())

        self.config.set(CONFIG_SECTION, ALLURE_IGNORE_PACKAGE_NAME, args.ignore_package_name)

        if args.alluredir:
            self.path_to_results = args.alluredir

        if args.set_rabbitmqhost:
            self.config.set(RABBITMQ_CONFIG_SECTION, RABBITMQ_CONFIG_URL, args.set_rabbitmqhost)

        if args.set_rabbitmquser:
            self.config.set(RABBITMQ_CONFIG_SECTION, RABBITMQ_CONFIG_USER, args.set_rabbitmquser)

        if args.set_rabbitmqpassword:
            self.config.set(RABBITMQ_CONFIG_SECTION, RABBITMQ_CONFIG_PASSWORD, args.set_rabbitmqpassword)

        if args.set_rabbitmqexchange:
            self.config.set(RABBITMQ_CONFIG_SECTION, RABBITMQ_CONFIG_EXCHANGE, args.set_rabbitmqexchange)

        if args.set_miniohost:
            self.config.set(MINIO_CONFIG_SECTION, MINIO_CONFIG_URL, args.set_miniohost)

        if args.set_minioaccesskey:
            self.config.set(MINIO_CONFIG_SECTION, MINIO_CONFIG_ACCESS_KEY, args.set_minioaccesskey)

        if args.set_miniosecretkey:
            self.config.set(MINIO_CONFIG_SECTION, MINIO_CONFIG_SECRET_KEY, args.set_miniosecretkey)

        if args.show_settings:
            print(
                f'url: {self.get_url()}\n'
                f'privatetoken: {self.get_private_token()}\n'
                f'projectID: {self.get_project_id()}\n'
                f'configurationID: {self.get_configuration_id()}')

        if args.set_url or args.set_privatetoken or args.set_project or args.set_configuration:
            with open(self.path_to_config, "w", encoding='utf-8') as config_file:
                self.config.write(config_file)
