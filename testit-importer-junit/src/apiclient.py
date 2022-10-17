"""The module provides functionality for working with TMS"""
from testit_api_client import JSONFixture
from testit_api_client.api import Api


class ApiClient:
    """Class representing a api client"""

    def __init__(self, url: str, token: str):
        self.__client = Api(url, token)

    def create_test_run(self, project_id: str, name: str):
        """Function creates test run and returns test run id."""
        return self.__client.create_testrun(JSONFixture.create_testrun(project_id, name))

    def upload_attachment(self, file):
        """Function uploads attachment and returns attachment id."""
        return self.__client.load_attachment(file)

    def get_autotest(self, autotest_id: str, project_id: str):
        """Function returns autotest."""
        return self.__client.get_autotest(autotest_id, project_id).json()

    def create_autotest(self, model: JSONFixture.create_autotest):
        """Function creates autotest and returns autotest id."""
        return self.__client.create_autotest(model)

    def update_autotest(self, model: JSONFixture.update_autotest):
        """Function updates autotest"""
        return self.__client.update_autotest(model)

    def link_autotest(self, autotest_id: str, work_item_id: str):
        """Function links autotest to test case"""
        self.__client.link_autotest(autotest_id, work_item_id)

    def send_test_result(self, testrun_id: str, model: JSONFixture.set_results_for_testrun):
        """Function sends autotest result to test run"""
        self.__client.set_results_for_testrun(testrun_id, [model])
