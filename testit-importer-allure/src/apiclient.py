"""The module provides functionality for working with TMS"""
import logging
import os
from typing import Any, Dict, List, Optional

from testit_api_client import ApiClient as TmsClient
from testit_api_client import Configuration
from testit_api_client.model.auto_test_api_result import AutoTestApiResult
from testit_api_client.models import (
    CreateEmptyRequest,
    LinkAutoTestToWorkItemRequest,
    AttachmentPutModel,
    ApiV2AutoTestsSearchPostRequest,
    AutoTestCreateApiModel,
    CreateAutoTestRequest,
    AutoTestUpdateApiModel,
    UpdateAutoTestRequest,
    AutoTestResultsForTestRunModel,
    DetailedProjectApiResult,
    WorkflowApiResult,
    CreateLinkApiModel,
    UpdateEmptyRequest,
    UpdateLinkApiModel,
    LinkType,
)
from testit_api_client.apis import TestRunsApi, AutoTestsApi, AttachmentsApi, ProjectsApi, WorkflowsApi
from .html_escape_utils import HtmlEscapeUtils
from .models.link_type import LinkType as ImporterLinkType
from .test_run_meta import merge_links, merge_tags


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
        self.__projects_api = ProjectsApi(api_client=client)
        self.__workflows_api = WorkflowsApi(api_client=client)

    def create_test_run(
            self,
            project_id: str,
            name: str,
            tags: Optional[List[str]] = None,
            links: Optional[List[Dict[str, Any]]] = None) -> str:
        """Function creates test run and returns test run id."""
        model = CreateEmptyRequest(
            project_id=project_id,
            name=name,
            tags=tags,
            links=self.__to_create_links(links) if links else None,
        )
        model = HtmlEscapeUtils.escape_html_in_object(model)
        response = self.__test_run_api.create_empty(create_empty_request=model)

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
            test_run = self.__test_run_api.get_test_run_by_id(id=test_run_id)
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

            model = UpdateEmptyRequest(
                id=test_run_id,
                name=test_run.name,
                description=test_run.description,
                launch_source=test_run.launch_source,
                tags=merged_tags,
                links=self.__to_update_links(merged_links),
            )
            model = HtmlEscapeUtils.escape_html_in_object(model)
            self.__test_run_api.update_empty(update_empty_request=model)

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
                has_info=True,
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
                'has_info': True,
            }
            if link.get('id'):
                kwargs['id'] = link['id']
            result.append(UpdateLinkApiModel(**kwargs))
        return result

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

    def get_autotest(self, model: ApiV2AutoTestsSearchPostRequest) -> List[AutoTestApiResult]:
        """Function returns autotest."""
        return self.__autotest_api.api_v2_auto_tests_search_post(
            api_v2_auto_tests_search_post_request=model)

    def create_autotest(self, model: CreateAutoTestRequest) -> str:
        """Function creates autotest and returns autotest id."""
        model = HtmlEscapeUtils.escape_html_in_object(model)
        response = self.__autotest_api.create_auto_test(create_auto_test_request=model)
        logging.info(f'Create "{model.name}" passed!')

        return response.id

    def create_autotests(self, models: List[AutoTestCreateApiModel]) -> None:
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

    def update_autotests(self, models: List[AutoTestUpdateApiModel]) -> None:
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

    def __send_test_results(self, testrun_id: str, test_results: List[AutoTestResultsForTestRunModel]) -> None:
        """Function sends autotest results to test run"""
        try:
            test_results = HtmlEscapeUtils.escape_html_in_object(test_results)
            self.__test_run_api.set_auto_test_results_for_test_run(
                id=testrun_id,
                auto_test_results_for_test_run_model=test_results)
            logging.info("Set results passed!")
        except Exception as exc:
            logging.error(f"Set results status: {exc}")

    def __get_project(self, project_id: str) -> DetailedProjectApiResult:
        """Function returns DetailedProjectApiResult."""
        return self.__projects_api.get_project_by_id(id=project_id)

    def __get_workflow_by_id(self, workflow_id: str) -> WorkflowApiResult:
        """Function returns WorkflowApiResult."""
        return self.__workflows_api.api_v2_workflows_id_get(id=workflow_id)

    def get_status_codes(self, project_id: str) -> List[str]:
        """Function returns list of statuses from project."""
        project: DetailedProjectApiResult = self.__get_project(project_id)
        workflow: WorkflowApiResult = self.__get_workflow_by_id(project.workflow_id)

        return [status.code for status in workflow.statuses]
