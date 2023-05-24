from testit_api_client.models import (
    AutoTestPostModel,
    AutoTestPutModel,
    AutoTestStepModel,
    AvailableTestResultOutcome,
    LinkPostModel,
    LinkPutModel,
    LinkType,
    AutoTestResultsForTestRunModel,
    AttachmentPutModelAutoTestStepResultsModel,
    LabelPostModel)


class Converter:
    @classmethod
    def test_result_to_autotest_post_model(
            cls,
            test_result: dict,
            project_id: str):
        return AutoTestPostModel(
            test_result['external_id'],
            project_id,
            test_result['name'],
            steps=cls.step_results_to_autotest_steps_model(test_result['steps']),
            setup=cls.step_results_to_autotest_steps_model(test_result['setup']),
            teardown=cls.step_results_to_autotest_steps_model(test_result['teardown']),
            namespace=test_result['namespace'],
            classname=test_result['classname'],
            description=test_result['description'],
            links=cls.links_to_links_post_model(test_result['links']),
            labels=test_result['labels']
        )

    @classmethod
    def test_result_to_autotest_put_model(
            cls,
            test_result: dict,
            project_id: str):
        return AutoTestPutModel(
            test_result['external_id'],
            project_id,
            test_result['name'],
            steps=cls.step_results_to_autotest_steps_model(test_result['steps']),
            setup=cls.step_results_to_autotest_steps_model(test_result['setup']),
            teardown=cls.step_results_to_autotest_steps_model(test_result['teardown']),
            namespace=test_result['namespace'],
            classname=test_result['classname'],
            description=test_result['description'],
            links=cls.links_to_links_put_model(test_result['links']),
            labels=test_result['labels'],
            is_flaky=test_result['is_flaky']
        )

    @classmethod
    def test_result_to_testrun_result_post_model(
            cls,
            test_result: dict,
            configuration_id: str):
        return AutoTestResultsForTestRunModel(
            configuration_id,
            test_result['external_id'],
            AvailableTestResultOutcome(test_result['outcome']),
            step_results=cls.step_results_to_attachment_put_model_autotest_step_results_model(
                test_result['step_results']),
            setup_results=cls.step_results_to_attachment_put_model_autotest_step_results_model(
                test_result['setup_results']),
            teardown_results=cls.step_results_to_attachment_put_model_autotest_step_results_model(
                test_result['teardown_results']),
            traces=test_result['traces'],
            attachments=test_result['attachments'],
            parameters=test_result['parameters'],
            links=cls.links_to_links_post_model(test_result['links']),
            duration=round(test_result['duration']),
            message=test_result['message'],
            started_on=test_result.get('started_on', None),
            completed_on=test_result.get('completed_on', None)
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
                url,
                title=title,
                type=url_type,
                description=description
            )
        else:
            return LinkPostModel(
                url,
                title=title,
                description=description
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
                url,
                title=title,
                type=url_type,
                description=description
            )
        else:
            return LinkPutModel(
                url,
                title=title,
                description=description
            )

    @classmethod
    def links_to_links_post_model(cls, links: list):
        post_model_links = []

        for link in links:
            post_model_links.append(cls.link_to_link_post_model(
                link['url'],
                link.get('title', None),
                link.get('type', None),
                link.get('description', None)
            ))

        return post_model_links

    @classmethod
    def links_to_links_put_model(cls, links: list):
        put_model_links = []

        for link in links:
            put_model_links.append(cls.link_to_link_put_model(
                link['url'],
                link.get('title', None),
                link.get('type', None),
                link.get('description', None)
            ))

        return put_model_links

    @classmethod
    def step_results_to_autotest_steps_model(cls, steps: list):
        autotest_model_steps = []

        for step in steps:
            autotest_model_steps.append(
                cls.step_result_to_autotest_step_model(
                    step['title'],
                    cls.step_results_to_autotest_steps_model(
                        step.get('steps', [])
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
    def step_results_to_attachment_put_model_autotest_step_results_model(cls, steps: list):
        autotest_model_step_results = []

        for step in steps:
            autotest_model_step_results.append(
                cls.step_result_to_attachment_put_model_autotest_step_results_model(
                    step['title'],
                    step['outcome'],
                    step['duration'],
                    step['parameters'],
                    step['attachments'],
                    cls.step_results_to_attachment_put_model_autotest_step_results_model(
                        step.get('step_results', [])
                    )
                )
            )

        return autotest_model_step_results

    @staticmethod
    def step_result_to_attachment_put_model_autotest_step_results_model(
            title: str,
            outcome: str,
            duration: str = None,
            parameters: list = None,
            attachments: list = None,
            step_results: list = None
    ):
        return AttachmentPutModelAutoTestStepResultsModel(
            title=title,
            outcome=AvailableTestResultOutcome(outcome),
            duration=duration,
            parameters=parameters,
            attachments=attachments,
            step_results=step_results
        )

    @staticmethod
    def label_to_label_post_model(label: str):
        return LabelPostModel(label)
