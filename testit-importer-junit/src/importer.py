from datetime import datetime
import hashlib

from testit_api_client import JSONFixture

from .apiclient import ApiClient
from .configurator import Configurator
from .parser import Parser


class Importer:

    def __init__(self, parser: Parser, api_client: ApiClient, config: Configurator):
        self.__parser = parser
        self.__api_client = api_client
        self.__config = config

    def send_results(self):
        if self.__config.get_test_run_id() is None:
            test_run_name = f'JunitRun {datetime.today().strftime("%d %b %Y %H:%M:%S")}'
            test_run_id = self.__api_client.create_test_run(self.__config.get_project_id(), test_run_name)
            self.__config.set_test_run_id(test_run_id)

        results = self.__parser.read_file()
        for result in results:
            external_id = self.__get_external_id(result.get_name_space() + result.get_class_name() + result.get_name())

            autotest = self.__api_client.get_autotest(external_id, self.__config.get_project_id())

            if not autotest:
                self.__api_client.create_autotest(
                    JSONFixture.create_autotest(
                        external_id,
                        self.__config.get_project_id(),
                        result.get_name(),
                        None,
                        None,
                        None,
                        result.get_name_space(),
                        result.get_class_name(),
                        None,
                        None,
                        None,
                        None
                    )
                )
            else:
                autotest_id = autotest[0]['id']
                self.__api_client.update_autotest(
                    JSONFixture.update_autotest(
                        external_id,
                        self.__config.get_project_id(),
                        result.get_name(),
                        autotest_id,
                        autotest[0]['steps'],
                        autotest[0]['setup'],
                        autotest[0]['teardown'],
                        result.get_name_space(),
                        result.get_class_name(),
                        None,
                        None,
                        None,
                        None
                    )
                )

            status = "Passed"
            if result.get_message() is not None:
                status = "Failed"

            self.__api_client.send_test_result(
                self.__config.get_test_run_id(),
                JSONFixture.set_results_for_testrun(
                    external_id,
                    self.__config.get_configuration_id(),
                    status,
                    None,
                    None,
                    None,
                    result.get_trace(),
                    None,
                    None,
                    None,
                    None,
                    result.get_duration(),
                    None,
                    result.get_message()
                )
            )

    @staticmethod
    def __get_external_id(value: str):
        return hashlib.md5(value.encode('utf-8')).hexdigest()
