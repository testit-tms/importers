"""The module provides functionality for working with TMS"""
import logging
import os
from typing import Any, Dict, List, Optional

from adapters_api import ApiClient as TmsClient
from adapters_api import Configuration
from adapters_api.apis import AttachmentsApi, AutoTestsApi, ProjectsApi, TestRunsApi
from adapters_api.model.adapters_auto_tests_id_work_items_post_request import (
    AdaptersAutoTestsIdWorkItemsPostRequest,
)
from adapters_api.model.adapters_auto_tests_post_request import AdaptersAutoTestsPostRequest
from adapters_api.model.adapters_auto_tests_put_request import AdaptersAutoTestsPutRequest
from adapters_api.model.adapters_auto_tests_search_post_request import (
    AdaptersAutoTestsSearchPostRequest,
)
from adapters_api.model.adapters_test_runs_post_request import AdaptersTestRunsPostRequest
from adapters_api.model.adapters_test_runs_put_request import AdaptersTestRunsPutRequest
from adapters_api.model.attachment_put_model import AttachmentPutModel
from adapters_api.model.auto_test_api_result import AutoTestApiResult
from adapters_api.model.auto_test_create_api_model import AutoTestCreateApiModel
from adapters_api.model.auto_test_results_for_test_run_model import AutoTestResultsForTestRunModel
from adapters_api.model.auto_test_update_api_model import AutoTestUpdateApiModel
from adapters_api.model.create_link_api_model import CreateLinkApiModel
from adapters_api.model.detailed_project_api_result import DetailedProjectApiResult
from adapters_api.model.link_type import LinkType
from adapters_api.model.update_link_api_model import UpdateLinkApiModel

from .html_escape_utils import HtmlEscapeUtils
from .models.link_type import LinkType as ImporterLinkType
from .test_run_meta import merge_links, merge_tags


# TODO: Use bulk-methods after refactoring the importer.py
class ApiClient:
    """Class representing a api client"""
    def __init__(self, url: str, token: str, cert_validation: str):
        client_config = Configuration(host=url)
        client_config.api_key['PrivateToken'] = token
        client_config.api_key_prefix['PrivateToken'] = 'PrivateToken'

        if cert_validation == 'false':
            client_config.verify_ssl = False

        client = TmsClient(configuration=client_config)
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
        self.__test_run_api = TestRunsApi(api_client=client)
        self.__autotest_api = AutoTestsApi(api_client=client)
        self.__attachments_api = AttachmentsApi(api_client=client)
        self.__projects_api = ProjectsApi(api_client=client)

    def create_test_run(
            self,
            project_id: str,
            name: str,
            tags: Optional[List[str]] = None,
            links: Optional[List[Dict[str, Any]]] = None) -> str:
        """Function creates test run and returns test run id."""
        model = AdaptersTestRunsPostRequest(
            project_id=project_id,
            name=name,
            tags=tags,
            links=self.__to_create_links(links) if links else None,
        )
        model = HtmlEscapeUtils.escape_html_in_object(model)
        response = self.__test_run_api.adapters_test_runs_post(
            adapters_test_runs_post_request=model)

        logging.info(
            f'Created test run "{response.id}"'
            f'{f" with tags={tags}" if tags else ""}'
            f'{f" with links={links}" if links else ""}'
        )

        return response.id

    def apply_test_run_tags_and_links(
            self,
            test_run_id: str,
            tags: Optional[List[str]] = None,
            links: Optional[List[Dict[str, Any]]] = None) -> None:
        """Merge configured tags/links into an existing test run as early as possible."""
        if not tags and not links:
            return

        try:
            test_run = self.__test_run_api.adapters_test_runs_id_get(id=test_run_id)
            existing_tags = list(test_run.tags or [])
            existing_links = [
                {
                    'url': item.url,
                    'title': item.title,
                    'description': item.description,
                    'type': str(item.type) if item.type is not None else ImporterLinkType.RELATED,
                    'id': item.id,
                }
                for item in (test_run.links or [])
            ]

            merged_tags = merge_tags(existing_tags, tags)
            merged_links = merge_links(existing_links, links)

            model = AdaptersTestRunsPutRequest(
                id=test_run_id,
                name=test_run.name,
                description=test_run.description,
                launch_source=test_run.launch_source,
                tags=merged_tags,
                links=self.__to_update_links(merged_links),
            )
            model = HtmlEscapeUtils.escape_html_in_object(model)
            self.__test_run_api.adapters_test_runs_put(
                adapters_test_runs_put_request=model)

            logging.info(
                f'Applied tags/links to test run "{test_run_id}": '
                f'tags={tags or []}, links={links or []}'
            )
        except Exception as exc:
            logging.error(f'Failed to apply tags/links to test run "{test_run_id}": {exc}')

    @staticmethod
    def __resolve_link_type(value: Optional[str]) -> LinkType:
        raw = value or ImporterLinkType.RELATED
        try:
            return LinkType(value=raw)
        except Exception:
            return LinkType(value=ImporterLinkType.RELATED)

    @classmethod
    def __to_create_links(cls, links: List[Dict[str, Any]]) -> List[CreateLinkApiModel]:
        return [
            CreateLinkApiModel(
                url=link['url'],
                title=link.get('title'),
                description=link.get('description'),
                type=cls.__resolve_link_type(link.get('type')),
            )
            for link in links
        ]

    @classmethod
    def __to_update_links(cls, links: List[Dict[str, Any]]) -> List[UpdateLinkApiModel]:
        result = []
        for link in links:
            kwargs = {
                'url': link['url'],
                'title': link.get('title'),
                'description': link.get('description'),
                'type': cls.__resolve_link_type(link.get('type')),
            }
            if link.get('id'):
                kwargs['id'] = link['id']
            result.append(UpdateLinkApiModel(**kwargs))
        return result

    def upload_attachment(self, path: str) -> AttachmentPutModel:
        if os.path.isfile(path):
            try:
                attachment_response = self.__attachments_api.adapters_attachments_post(
                    file=open(path, "rb"))

                logging.debug(f'Attachment "{path}" was uploaded')

                return AttachmentPutModel(id=attachment_response.id)
            except Exception as exc:
                logging.error(f'Upload attachment "{path}" status: {exc}')
        else:
            logging.error(f'File "{path}" was not found!')

    def get_autotest(self, model: AdaptersAutoTestsSearchPostRequest) -> List[AutoTestApiResult]:
        """Function returns autotest."""
        return self.__autotest_api.adapters_auto_tests_search_post(
            adapters_auto_tests_search_post_request=model)

    def create_autotest(self, model: AdaptersAutoTestsPostRequest) -> str:
        """Function creates autotest and returns autotest id."""
        model = HtmlEscapeUtils.escape_html_in_object(model)
        response = self.__autotest_api.adapters_auto_tests_post(
            adapters_auto_tests_post_request=model)
        logging.info(f'Create "{model.name}" passed!')

        return response.id

    def create_autotests(self, models: List[AutoTestCreateApiModel]) -> None:
        """Function creates autotests"""
        models = HtmlEscapeUtils.escape_html_in_object(models)
        logging.debug(f'Creating autotests: "{models}')

        self.__autotest_api.adapters_auto_tests_bulk_post(auto_test_create_api_model=models)

        logging.info(f'Create {len(models)} autotests passed!')

    def update_autotest(self, model: AdaptersAutoTestsPutRequest) -> None:
        """Function updates autotest"""
        try:
            model = HtmlEscapeUtils.escape_html_in_object(model)
            self.__autotest_api.adapters_auto_tests_put(
                adapters_auto_tests_put_request=model)
            logging.info(f'Update "{model.name}" passed!')
        except Exception as exc:
            logging.error(f'Update "{model.name}" status: {exc}')

    def update_autotests(self, models: List[AutoTestUpdateApiModel]) -> None:
        """Function updates autotests"""
        try:
            models = HtmlEscapeUtils.escape_html_in_object(models)
            logging.debug(f'Updating autotests: {models}')

            self.__autotest_api.adapters_auto_tests_bulk_put(auto_test_update_api_model=models)

            logging.info(f'Update {len(models)} autotests passed!')
        except Exception as exc:
            logging.error(f'Update {len(models)} autotests status: {exc}')

    def link_autotest(self, autotest_id: str, work_item_id: str) -> None:
        """Function links autotest to test case"""
        try:
            self.__autotest_api.adapters_auto_tests_id_work_items_post(
                autotest_id,
                adapters_auto_tests_id_work_items_post_request=AdaptersAutoTestsIdWorkItemsPostRequest(
                    id=work_item_id))
            logging.info(f'Link with WI "{work_item_id}" passed!')
        except Exception as exc:
            logging.error(f'Link with WI "{work_item_id}" status: {exc}')

    def send_test_result(self, testrun_id: str, model: AutoTestResultsForTestRunModel) -> None:
        """Function sends autotest result to test run"""
        model = HtmlEscapeUtils.escape_html_in_object(model)
        self.__test_run_api.adapters_test_runs_id_test_results_post(
            id=testrun_id,
            auto_test_results_for_test_run_model=[model])
        logging.info("Set result passed!")

    def __send_test_results(self, testrun_id: str, test_results: List[AutoTestResultsForTestRunModel]) -> None:
        """Function sends autotest results to test run"""
        try:
            test_results = HtmlEscapeUtils.escape_html_in_object(test_results)
            self.__test_run_api.adapters_test_runs_id_test_results_post(
                id=testrun_id,
                auto_test_results_for_test_run_model=test_results)
            logging.info("Set results passed!")
        except Exception as exc:
            logging.error(f"Set results status: {exc}")

    def get_status_codes(self, project_id: str) -> List[str]:
        """Function returns list of statuses from project."""
        project: DetailedProjectApiResult = self.__projects_api.adapters_projects_id_get(
            id=project_id)
        statuses = project.workflow.statuses if project.workflow else []

        return [status.code for status in statuses]
