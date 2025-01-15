"""The module provides functionality for working with TMS"""
import logging

from testit_api_client import ApiClient as TmsClient
from testit_api_client import Configuration
from testit_api_client.models import (
    TestRunV2PostShortModel,
    WorkItemIdModel,
    AttachmentPutModel
)
from testit_api_client.api import TestRunsApi, AutoTestsApi, AttachmentsApi

from .converter import Converter


class ApiClient:
    """Class representing a api client"""
    def __init__(self, url: str, token: str, cert_validation: str):
        client_config = Configuration(host=url)

        if cert_validation == 'false':
            client_config.verify_ssl = False

        client = TmsClient(
            configuration=client_config,
            header_name='Authorization',
            header_value='PrivateToken ' + token
        )
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
        self.__test_run_api = TestRunsApi(api_client=client)
        self.__autotest_api = AutoTestsApi(api_client=client)
        self.__attachments_api = AttachmentsApi(api_client=client)

    def create_test_run(self, project_id: str, name: str):
        """Function creates test run and returns test run id."""
        model = TestRunV2PostShortModel(
            project_id=project_id,
            name=name
        )
        response = self.__test_run_api.create_empty(test_run_v2_post_short_model=model)

        return response.id

    def upload_attachment(self, file):
        with file:
            try:
                attachment_response = self.__attachments_api.api_v2_attachments_post(
                    file=(file.name, file.read()))

                logging.debug(f'Attachment "{file}" was uploaded')

                return AttachmentPutModel(id=attachment_response.id)
            except Exception as exc:
                logging.error(f'Upload attachment "{file}" status: {exc}')

    def get_autotest(self, model: Converter.project_id_and_external_id_to_autotests_select_model):
        """Function returns autotest."""
        return self.__autotest_api.api_v2_auto_tests_search_post(
            autotests_select_model=model)

    def create_autotest(self, model: Converter.test_result_to_autotest_post_model):
        """Function creates autotest and returns autotest id."""
        response = self.__autotest_api.create_auto_test(auto_test_post_model=model)
        logging.info(f'Create "{model.name}" passed!')

        return response.id

    def update_autotest(self, model: Converter.test_result_to_autotest_put_model):
        """Function updates autotest"""
        try:
            self.__autotest_api.update_auto_test(auto_test_put_model=model)
            logging.info(f'Update "{model.name}" passed!')
        except Exception as exc:
            logging.error(f'Update "{model.name}" status: {exc}')

    def link_autotest(self, autotest_id: str, work_item_id: str):
        """Function links autotest to test case"""
        try:
            self.__autotest_api.link_auto_test_to_work_item(
                autotest_id,
                work_item_id_model=WorkItemIdModel(id=work_item_id))
            logging.info(f'Link with WI "{work_item_id}" passed!')
        except Exception as exc:
            logging.error(f'Link with WI "{work_item_id}" status: {exc}')

    def send_test_result(self, testrun_id: str, model: Converter.test_result_to_testrun_result_post_model):
        """Function sends autotest result to test run"""
        try:
            self.__test_run_api.set_auto_test_results_for_test_run(
                id=testrun_id,
                auto_test_results_for_test_run_model=[model])
            logging.info("Set result passed!")
        except Exception as exc:
            logging.error(f"Set result status: {exc}")
