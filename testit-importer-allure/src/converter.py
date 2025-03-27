import typing
from datetime import datetime

from testit_api_client.models import (
    AutoTestModel,
    AutoTestPostModel,
    AutoTestPutModel,
    AutoTestStepModel,
    AvailableTestResultOutcome,
    AutoTestFilterApiModel,
    AutoTestSearchIncludeApiModel,
    AutoTestSearchApiModel,
    LinkPostModel,
    LinkPutModel,
    LinkType,
    AutoTestResultsForTestRunModel,
    AttachmentPutModelAutoTestStepResultsModel,
    LabelPostModel)

from .models import Link, StepResult, TestResult


class Converter:
    @classmethod
    def project_id_and_external_id_to_autotests_select_model(cls, project_id: str, external_id: str):
        autotests_filter = AutoTestFilterApiModel(
            project_ids=[project_id],
            external_ids=[external_id],
            is_deleted=False)
        autotests_includes = AutoTestSearchIncludeApiModel(
            include_steps=False,
            include_links=False,
            include_labels=False)

        return AutoTestSearchApiModel(filter=autotests_filter, includes=autotests_includes)

    @classmethod
    def test_result_to_autotest_post_model(
            cls,
            test_result: TestResult,
            project_id: str):
        return AutoTestPostModel(
            external_id=test_result.get_external_id(),
            project_id=project_id,
            name=test_result.get_title(),
            steps=cls.step_results_to_autotest_steps_model(test_result.get_step_results()),
            setup=cls.step_results_to_autotest_steps_model(test_result.get_setup_results()),
            teardown=cls.step_results_to_autotest_steps_model(test_result.get_teardown_results()),
            namespace=test_result.get_namespace(),
            classname=test_result.get_classname(),
            description=test_result.get_description(),
            links=cls.links_to_links_post_model(test_result.get_links()),
            labels=test_result.get_labels()
        )

    @classmethod
    def test_result_to_autotest_put_model(
            cls,
            test_result: TestResult,
            project_id: str):
        return AutoTestPutModel(
            external_id=test_result.get_external_id(),
            project_id=project_id,
            name=test_result.get_title(),
            steps=cls.step_results_to_autotest_steps_model(test_result.get_step_results()),
            setup=cls.step_results_to_autotest_steps_model(test_result.get_setup_results()),
            teardown=cls.step_results_to_autotest_steps_model(test_result.get_teardown_results()),
            namespace=test_result.get_namespace(),
            classname=test_result.get_classname(),
            description=test_result.get_description(),
            links=cls.links_to_links_put_model(test_result.get_links()),
            labels=test_result.get_labels(),
            is_flaky=test_result.get_is_flaky(),
        )

    @classmethod
    def auto_test_model_to_update_autotest_put_model(
            cls,
            auto_test_model: AutoTestModel,
            project_id: str):
        return AutoTestPutModel(
            external_id=auto_test_model.external_id,
            project_id=project_id,
            name=auto_test_model.name,
            steps=auto_test_model.steps,
            setup=auto_test_model.setup,
            teardown=auto_test_model.teardown,
            namespace=auto_test_model.namespace,
            classname=auto_test_model.classname,
            description=auto_test_model.description,
            links=auto_test_model.links,
            labels=auto_test_model.labels,
            is_flaky=auto_test_model.is_flaky,
        )

    @classmethod
    def test_result_to_testrun_result_post_model(
            cls,
            test_result: TestResult,
            configuration_id: str):
        return AutoTestResultsForTestRunModel(
            configuration_id=configuration_id,
            auto_test_external_id=test_result.get_external_id(),
            outcome=AvailableTestResultOutcome(test_result.get_outcome()),
            step_results=cls.step_results_to_attachment_put_model_autotest_step_results_model(
                test_result.get_step_results()),
            setup_results=cls.step_results_to_attachment_put_model_autotest_step_results_model(
                test_result.get_setup_results()),
            teardown_results=cls.step_results_to_attachment_put_model_autotest_step_results_model(
                test_result.get_teardown_results()),
            traces=test_result.get_traces(),
            attachments=test_result.get_attachments(),
            parameters=test_result.get_parameters(),
            links=cls.links_to_links_post_model(test_result.get_links()),
            duration=round(test_result.get_duration()),
            message=test_result.get_message(),
            started_on=test_result.get_started_on(),
            completed_on=test_result.get_completed_on(),
        )

    @staticmethod
    def link_to_link_post_model(
            url: str,
            title: str,
            url_type,
            description: str):
        if url_type:
            if type(url_type) is str:
                url_type = LinkType(value=url_type)
            return LinkPostModel(
                url=url,
                title=title,
                type=url_type,
                description=description,
                has_info=True,
            )
        else:
            return LinkPostModel(
                url=url,
                title=title,
                description=description,
                has_info=True,
            )

    @staticmethod
    def link_to_link_put_model(
            url: str,
            title: str,
            url_type,
            description: str):
        if url_type:
            if type(url_type) is str:
                url_type = LinkType(value=url_type)
            return LinkPutModel(
                url=url,
                title=title,
                type=url_type,
                description=description,
                has_info=True,
            )
        else:
            return LinkPutModel(
                url=url,
                title=title,
                description=description,
                has_info=True,
            )

    @classmethod
    def links_to_links_post_model(cls, links: typing.List[Link]):
        post_model_links = []

        for link in links:
            post_model_links.append(cls.link_to_link_post_model(
                link.get_url(),
                link.get_title(),
                link.get_link_type(),
                link.get_description()
            ))

        return post_model_links

    @classmethod
    def links_to_links_put_model(cls, links: typing.List[Link]):
        put_model_links = []

        for link in links:
            put_model_links.append(cls.link_to_link_put_model(
                link.get_url(),
                link.get_title(),
                link.get_link_type(),
                link.get_description()
            ))

        return put_model_links

    @classmethod
    def step_results_to_autotest_steps_model(cls, steps: typing.List[StepResult]):
        autotest_model_steps = []

        for step in steps:
            autotest_model_steps.append(
                cls.step_result_to_autotest_step_model(
                    step.get_title(),
                    cls.step_results_to_autotest_steps_model(
                        step.get_step_results()
                    )
                )
            )

        return autotest_model_steps

    @staticmethod
    def step_result_to_autotest_step_model(
            title: str,
            steps: list = None):
        return AutoTestStepModel(
            title=title,
            steps=steps)

    @classmethod
    def step_results_to_attachment_put_model_autotest_step_results_model(cls, steps: typing.List[StepResult]):
        autotest_model_step_results = []

        for step in steps:
            autotest_model_step_results.append(
                cls.step_result_to_attachment_put_model_autotest_step_results_model(
                    step.get_title(),
                    step.get_outcome(),
                    step.get_duration(),
                    step.get_started_on(),
                    step.get_completed_on(),
                    step.get_parameters(),
                    step.get_attachments(),
                    cls.step_results_to_attachment_put_model_autotest_step_results_model(
                        step.get_step_results()
                    )
                )
            )

        return autotest_model_step_results

    @staticmethod
    def step_result_to_attachment_put_model_autotest_step_results_model(
            title: str,
            outcome: str,
            duration: int,
            started_on: datetime,
            completed_on: datetime,
            parameters: dict,
            attachments: typing.List[str],
            step_results: typing.List[AttachmentPutModelAutoTestStepResultsModel]
    ):
        return AttachmentPutModelAutoTestStepResultsModel(
            title=title,
            outcome=AvailableTestResultOutcome(outcome),
            duration=duration,
            parameters=parameters,
            attachments=attachments,
            step_results=step_results,
            started_on=started_on,
            completed_on=completed_on,
        )

    @staticmethod
    def label_to_label_post_model(label: str):
        return LabelPostModel(name=label)
