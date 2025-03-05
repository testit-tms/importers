"""The module provides functionality for importing result to TMS"""
import re
import dataclasses
from datetime import datetime
from .apiclient import ApiClient
from .configurator import Configurator
from .parser import Parser
from .converter import Converter
from .models import Link, LinkType, StepResult, TestResult


# TODO: Refactoring after adding parsing models
@dataclasses.dataclass
class Importer:
    """Class representing an importer"""

    def __init__(self, parser: Parser, api_client: ApiClient, config: Configurator):
        self.__parser = parser
        self.__api_client = api_client
        self.__project_id = config.get_project_id()
        self.__testrun_id = config.specified_testrun
        self.__testrun_name = config.specified_testrun_name
        self.__configuration_id = config.get_configuration_id()
        self.__ignore_namespace_name = config.get_ignore_package_name()
        self.__include_reruns = config.get_include_reruns()

    def send_result(self):
        """Function imports result to TMS."""
        data_tests, data_containers = self.__parser.parse_results()
        data_fixtures = self.__form_fixtures(data_containers)

        self.__set_test_run()

        for history_id in data_tests:
            test_results = data_tests[history_id]
            sorted_test_results_by_start = sorted(
                test_results, key=lambda test_result: test_result[('' if 'uuid' in test_result else '@') + 'start'])

            if self.__include_reruns:
                self.__send_test_results(sorted_test_results_by_start, data_fixtures, history_id)

                continue

            self.__send_test_results(sorted_test_results_by_start[-1:], data_fixtures, history_id)

    def __send_test_results(self, test_results, data_fixtures, history_id):
        for test_result in test_results:
            self.__send_test_result(test_result, data_fixtures, history_id)

    def __send_test_result(self, test, data_fixtures, history_id):
        test_result = self.__form_test_result(test, data_fixtures, history_id)

        autotest = self.__api_client.get_autotest(
            Converter.project_id_and_external_id_to_autotests_select_model(
                self.__project_id,
                test_result.get_external_id())
        )

        if not autotest:
            autotest_id = self.__api_client.create_autotest(
                Converter.test_result_to_autotest_post_model(test_result, self.__project_id)
            )
        else:
            autotest_id = autotest[0].id

            if test_result.get_outcome() == 'Passed':
                test_result.set_is_flaky(autotest[0].is_flaky)

                self.__api_client.update_autotest(
                    Converter.test_result_to_autotest_put_model(test_result, self.__project_id)
                )
            else:
                autotest[0].links = Converter.links_to_links_put_model(test_result.get_links())

                for i in range(0, len(autotest[0].labels)):
                    autotest[0].labels[i] = \
                        Converter.label_to_label_post_model(autotest[0].labels[i].name)

                self.__api_client.update_autotest(
                    Converter.auto_test_model_to_update_autotest_put_model(autotest[0], self.__project_id)
                )

        for work_item_id in test_result.get_work_item_ids():
            self.__api_client.link_autotest(autotest_id, work_item_id)

        self.__api_client.send_test_result(
            self.__testrun_id,
            Converter.test_result_to_testrun_result_post_model(test_result, self.__configuration_id)
        )

    def __form_test_result(self, test, data_fixtures, history_id) -> TestResult:
        prefix = '' if 'uuid' in test else '@'
        test_result = TestResult()

        if 'name' not in test and 'fullName' in test:
            test['name'] = test['fullName']

        step_results = self.__form_steps(test.get('steps', None))
        started_on = datetime.fromtimestamp(int(test[prefix + 'start']) / 1000.0)
        completed_on = datetime.fromtimestamp(int(test[prefix + 'stop']) / 1000.0)
        title = test['name']
        description = self.__get_description(test.get('description', None))
        outcome = 'Blocked'

        if prefix + 'status' in test:
            outcome = test[prefix + 'status'].title() if test[prefix + 'status'] in ('passed', 'skipped') else 'Failed'

        test_result \
            .set_external_id(history_id) \
            .set_outcome(outcome) \
            .set_title(title) \
            .set_description(description) \
            .set_step_results(step_results) \
            .set_started_on(started_on) \
            .set_completed_on(completed_on)

        if 'labels' in test:
            self.__set_data_from_labels(test_result, test['labels'])

        if 'attachments' in test:
            attachment_ids = self.__send_attachments(test['attachments'])

            test_result.set_attachments(attachment_ids)

        self.__form_setup_teardown(test_result, data_fixtures, test.get('uuid', None), prefix)

        if 'links' in test:
            links = self.__form_links(test['links'])

            test_result.set_links(links)

        if 'statusDetails' in test and test['statusDetails']:
            traces = test['statusDetails'].get('trace')

            test_result.set_traces(traces)

            if 'message' in test['statusDetails']:
                message = test['statusDetails']['message']

                test_result.set_message(message)

        if 'parameters' in test:
            parameters = self.__form_parameters(test['parameters'])

            test_result.set_parameters(parameters)

        if prefix + 'stop' in test:
            duration = (int(test[prefix + 'stop']) - int(test[prefix + 'start']))

            test_result.set_duration(duration)

        return test_result

    def __set_test_run(self):
        if self.__testrun_id is None:
            if self.__testrun_name is not None:
                test_run_name = f'{self.__testrun_name} {datetime.today().strftime("%d %b %Y %H:%M:%S")}'
            else:
                test_run_name = f'AllureRun {datetime.today().strftime("%d %b %Y %H:%M:%S")}'
            self.__testrun_id = self.__api_client.create_test_run(self.__project_id, test_run_name)

    def __send_attachments(self, attachments):
        attachment_ids = []

        if attachments:
            if 'attachment' in attachments:
                if type(attachments['attachment']) != list:
                    attachments = [attachments['attachment']]
                else:
                    attachments = attachments['attachment']

            prefix = '' if 'source' in attachments[0] else '@'

            for attachment in attachments:

                file = self.__parser.parse_attachment(f"{attachment[prefix + 'source']}")

                if file is None:
                    continue

                attachment_id = self.__api_client.upload_attachment(file)

                if attachment_id:
                    attachment_ids.append(attachment_id)

                self.__parser.clean_attachment(f"{attachment[prefix + 'source']}")

        return attachment_ids

    @staticmethod
    def __get_description(allure_description):
        if type(allure_description) == 'str':
            return allure_description
        elif type(allure_description) == 'dict':
            return allure_description.get('#text', None)

        return None

    def __set_data_from_labels(self, test_result: TestResult, allure_labels):
        class_name = None
        namespace = None
        labels = []
        work_item_ids = []

        if allure_labels:
            allure_labels, prefix = self.__parse_xml(allure_labels, 'label', 'value')

            for label in allure_labels:
                if label[prefix + 'name'] == 'testcase':
                    work_item_ids.append(label[prefix + 'value'])
                else:
                    labels.append(
                        Converter.label_to_label_post_model(
                            f"{label[prefix + 'name']}::{label[prefix + 'value']}"))

                if label[prefix + 'name'] == 'package' and not self.__ignore_namespace_name:
                    packages = label[prefix + 'value'].split('.')

                    while packages and not packages[-1]:
                        del packages[-1]

                    if packages:
                        namespace = packages[-1]
                elif label[prefix + 'name'] == 'parentSuite' and label[prefix + 'value']:
                    namespace = label[prefix + 'value']
                elif label[prefix + 'name'] in ('subSuite', 'suite') and label[prefix + 'value']:
                    class_name = label[prefix + 'value']
                elif label[prefix + 'name'] == 'testClass' and label[prefix + 'value'].split('.')[-1]:
                    class_name = label[prefix + 'value'].split('.')[-1]

        test_result\
            .set_labels(labels)\
            .set_namespace(namespace)\
            .set_classname(class_name)\
            .set_work_item_ids(work_item_ids)

    @staticmethod
    def __parse_xml(data, key, value):
        if key in data:
            if type(data[key]) != list:
                data = [data[key]]
            else:
                data = data[key]

        prefix = '' if data and value in data[0] else '@'

        return data, prefix

    @staticmethod
    def __form_links(allure_links):
        links = []

        if allure_links:
            for allure_link in allure_links:
                link = Link()

                if 'url' in allure_link and re.fullmatch(
                        r'^(?:(?:(?:https?|ftp):)?\/\/)?(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-zA-Z0-9\u00a1-\uffff][a-zA-Z0-9\u00a1-\uffff_-]{0,62})?[a-zA-Z0-9\u00a1-\uffff]\.?)+(?:[a-zA-Z\u00a1-\uffff]{2,}\.?))(?::\d{2,5})?(?:[/?#]\S*)?$',
                        allure_link['url']):
                    link.set_url(allure_link['url'])
                else:
                    raise Exception('Some links have the wrong URL or no URL!')

                if 'type' in allure_link and allure_link['type'].title() in (
                        LinkType.RELATED,
                        LinkType.BLOCKED_BY,
                        LinkType.DEFECT,
                        LinkType.ISSUE,
                        LinkType.REQUIREMENT,
                        LinkType.REPOSITORY):
                    link.set_link_type(allure_link['type'].title())

                if 'name' in allure_link:
                    link.set_title(str(allure_link['name']))

                links.append(link)

        return links

    def __form_steps(self, steps):
        step_results = []

        if steps:
            steps, prefix = self.__parse_xml(steps, 'step', 'status')

            sorted_steps_by_start = sorted(steps, key=lambda s: s[prefix + 'start'])

            for step in sorted_steps_by_start:
                if 'name' not in step:
                    continue

                attachment_ids = self.__send_attachments(step['attachments']) if 'attachments' in step else []
                outcome = step[prefix + 'status'].title() if \
                    prefix + 'status' in step and step[prefix + 'status'] in ('passed', 'skipped') else 'Failed'

                step_result = StepResult()

                step_result\
                    .set_title(step['name'])\
                    .set_outcome(outcome)\
                    .set_attachments(attachment_ids)

                if 'steps' in step:
                    inner_results_step_results = self.__form_steps(step['steps'])

                    step_result.set_step_results(inner_results_step_results)

                if prefix + 'start' in step:
                    started_on = datetime.fromtimestamp(int(step[prefix + 'start']) / 1000.0)

                    step_result.set_started_on(started_on)

                if prefix + 'stop' in step:
                    completed_on = datetime.fromtimestamp(int(step[prefix + 'stop']) / 1000.0)
                    duration = int(step[prefix + 'stop']) - int(step[prefix + 'start'])

                    step_result\
                        .set_completed_on(completed_on)\
                        .set_duration(duration)

                if 'parameters' in step:
                    parameters = self.__form_parameters(step['parameters'])

                    step_result.set_parameters(parameters)

                step_results.append(step_result)

        return step_results

    def __form_parameters(self, allure_parameters):
        parameters = {}

        if allure_parameters:
            allure_parameters, prefix = self.__parse_xml(allure_parameters, 'parameter', 'value')

            for parameter in allure_parameters:
                if parameter is None:
                    continue

                parameters[parameter[prefix + 'name']] = str(parameter[prefix + 'value']) if prefix + 'value' in parameter else ''

        return parameters

    def __form_fixtures(self, data_containers: dict) -> dict:
        data_fixtures = {}

        for container in data_containers.values():
            container['befores'] = self.__form_steps(container.get('befores'))
            container['afters'] = self.__form_steps(container.get('afters'))

            for test_uuid in container['children']:
                if test_uuid not in data_fixtures.keys():
                    data_fixtures[test_uuid] = []

                data_fixtures[test_uuid].append(container)

        return data_fixtures

    @staticmethod
    def __form_setup_teardown(test_result: TestResult, data_fixtures: dict, test_uuid: str, prefix: str):
        setup_results = []
        teardown_results = []

        if test_uuid and test_uuid in data_fixtures:
            fixtures_for_test = data_fixtures[test_uuid]
            sorted_fixtures_for_test_by_start = sorted(
                fixtures_for_test, key=lambda f: f[prefix + 'start'])

            for fixture in sorted_fixtures_for_test_by_start:
                step_results = fixture.get('befores')
                setup_results += step_results
                step_results = fixture.get('afters')
                teardown_results = step_results + teardown_results

        test_result\
            .set_setup_results(setup_results)\
            .set_teardown_results(teardown_results)
