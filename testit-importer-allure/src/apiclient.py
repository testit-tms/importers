"""The module provides functionality for working with TMS"""
import logging
import os
import typing

from testit_api_client import ApiClient as TmsClient
from testit_api_client import Configuration
from testit_api_client.model.auto_test_api_result import AutoTestApiResult
from testit_api_client.models import (
    CreateEmptyRequest,
    LinkAutoTestToWorkItemRequest,
    AttachmentPutModel,
    ApiV2AutoTestsSearchPostRequest,
    AutoTestPostModel,
    CreateAutoTestRequest,
    AutoTestPutModel,
    UpdateAutoTestRequest,
    AutoTestResultsForTestRunModel,
)
from testit_api_client.apis import TestRunsApi, AutoTestsApi, AttachmentsApi
from .html_escape_utils import HtmlEscapeUtils


# TODO: Use bulk-methods after refactoring the importer.py
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

    def create_test_run(self, project_id: str, name: str) -> str:
        """Function creates test run and returns test run id."""
        model = CreateEmptyRequest(
            project_id=project_id,
            name=name
        )
        model = HtmlEscapeUtils.escape_html_in_object(model)
        response = self.__test_run_api.create_empty(create_empty_request=model)

        return response.id

    def upload_attachment(self, path: str) -> AttachmentPutModel:
        if os.path.isfile(path):
            try:
                attachment_response = self.__attachments_api.api_v2_attachments_post(file=open(path, "rb"))

                logging.debug(f'Attachment "{path}" was uploaded')

                return AttachmentPutModel(id=attachment_response.id)
            except Exception as exc:
                logging.error(f'Upload attachment "{path}" status: {exc}')
        else:
            logging.error(f'File "{path}" was not found!')

    def get_autotest(self, model: ApiV2AutoTestsSearchPostRequest) -> typing.List[AutoTestApiResult]:
        """Function returns autotest."""
        return self.__autotest_api.api_v2_auto_tests_search_post(
            api_v2_auto_tests_search_post_request=model)

    def create_autotest(self, model: CreateAutoTestRequest) -> str:
        """Function creates autotest and returns autotest id."""
        model = HtmlEscapeUtils.escape_html_in_object(model)
        response = self.__autotest_api.create_auto_test(create_auto_test_request=model)
        logging.info(f'Create "{model.name}" passed!')

        return response.id

    def create_autotests(self, models: typing.List[AutoTestPostModel]) -> None:
        """Function creates autotests"""
        models = HtmlEscapeUtils.escape_html_in_object(models)
        logging.debug(f'Creating autotests: "{models}')

        self.__autotest_api.create_multiple(auto_test_post_model=models)

        logging.info(f'Create {len(models)} autotests passed!')

    def update_autotest(self, model: UpdateAutoTestRequest) -> None:
        """Function updates autotest"""
        try:
            model = HtmlEscapeUtils.escape_html_in_object(model)
            self.__autotest_api.update_auto_test(update_auto_test_request=model)
            logging.info(f'Update "{model.name}" passed!')
        except Exception as exc:
            logging.error(f'Update "{model.name}" status: {exc}')

    def update_autotests(self, models: typing.List[AutoTestPutModel]) -> None:
        """Function updates autotests"""
        try:
            models = HtmlEscapeUtils.escape_html_in_object(models)
            logging.debug(f'Updating autotests: {models}')

            self.__autotest_api.update_multiple(auto_test_put_model=models)

            logging.info(f'Update {len(models)} autotests passed!')
        except Exception as exc:
            logging.error(f'Update {len(models)} autotests status: {exc}')

    def link_autotest(self, autotest_id: str, work_item_id: str) -> None:
        """Function links autotest to test case"""
        try:
            self.__autotest_api.link_auto_test_to_work_item(
                autotest_id,
                link_auto_test_to_work_item_request=LinkAutoTestToWorkItemRequest(id=work_item_id))
            logging.info(f'Link with WI "{work_item_id}" passed!')
        except Exception as exc:
            logging.error(f'Link with WI "{work_item_id}" status: {exc}')

    def send_test_result(self, testrun_id: str, model: AutoTestResultsForTestRunModel) -> None:
        """Function sends autotest result to test run"""
        try:
            model = HtmlEscapeUtils.escape_html_in_object(model)
            self.__test_run_api.set_auto_test_results_for_test_run(
                id=testrun_id,
                auto_test_results_for_test_run_model=[model])
            logging.info("Set result passed!")
        except Exception as exc:
            logging.error(f"Set result status: {exc}")

    def __send_test_results(self, testrun_id: str, test_results: typing.List[AutoTestResultsForTestRunModel]) -> None:
        """Function sends autotest results to test run"""
        try:
            test_results = HtmlEscapeUtils.escape_html_in_object(test_results)
            self.__test_run_api.set_auto_test_results_for_test_run(
                id=testrun_id,
                auto_test_results_for_test_run_model=test_results)
            logging.info("Set results passed!")
        except Exception as exc:
            logging.error(f"Set results status: {exc}")
