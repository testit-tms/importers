"""The module provides functionality for importing result to TMS"""
import re
import dataclasses
from datetime import datetime
from testit_api_client import JSONFixture
from .apiclient import ApiClient
from .configurator import Configurator
from .parser import Parser


@dataclasses.dataclass
class Importer:
    """Class representing an importer"""

    def __init__(self, parser: Parser, api_client: ApiClient, config: Configurator):
        self.__parser = parser
        self.__api_client = api_client
        self.__project_id = config.get_project_id()
        self.__testrun_id = config.specified_testrun
        self.__configuration_id = config.get_configuration_id()

    def send_result(self):
        """Function imports result to TMS."""
        steps = []
        results_steps = []

        data_tests, data_fixtures = self.__parser.parse_results()

        self.__set_test_run()

        for history_id in data_tests:

            test = data_tests[history_id]
            prefix = '' if 'uuid' in test else '@'

            labels, namespace, class_name, work_items_id = self.__get_data_from_labels(test['labels'])
            attachments = self.__send_attachments(test['attachments']) if 'attachments' in test else []

            setup, results_setup, teardown, results_teardown = \
                self.__form_setup_teardown(data_fixtures, test['uuid'] if 'uuid' in test else None)

            if 'steps' in test:
                steps, results_steps = self.__form_steps(test['steps'])

            links = self.__form_links(test['links']) if 'links' in test else []

            if f'{prefix}status' in test:
                outcome = \
                    test[f'{prefix}status'].title() if test[f'{prefix}status'] in ('passed', 'skipped') else 'Failed'
            else:
                outcome = 'Blocked'

            autotest = self.__api_client.get_autotest(history_id, self.__project_id)

            if not autotest:
                autotest_id = self.__api_client.create_autotest(
                    JSONFixture.create_autotest(
                        history_id,
                        self.__project_id,
                        test['name'],
                        steps,
                        setup,
                        teardown,
                        namespace,
                        class_name,
                        None,
                        test['description'] if 'description' in test else None,
                        links,
                        labels
                    )
                )
            else:
                autotest_id = autotest[0]['id']

                if outcome == 'Passed':
                    self.__api_client.update_autotest(
                        JSONFixture.update_autotest(
                            history_id,
                            self.__project_id,
                            test['name'],
                            autotest_id,
                            steps,
                            setup,
                            teardown,
                            namespace,
                            class_name,
                            None,
                            test['description'] if 'description' in test else None,
                            links,
                            labels
                        )
                    )
                else:
                    self.__api_client.update_autotest(
                        JSONFixture.update_autotest(
                            history_id,
                            self.__project_id,
                            autotest[0]['name'],
                            autotest_id,
                            autotest[0]['steps'],
                            autotest[0]['setup'],
                            autotest[0]['teardown'],
                            autotest[0]['namespace'],
                            autotest[0]['classname'],
                            autotest[0]['title'],
                            autotest[0]['description'],
                            links,
                            autotest[0]['labels']
                        )
                    )

            for work_item_id in work_items_id:
                self.__api_client.link_autotest(autotest_id, work_item_id)

            self.__api_client.send_test_result(
                self.__testrun_id,
                JSONFixture.set_results_for_testrun(
                    history_id,
                    self.__configuration_id,
                    outcome,
                    results_steps,
                    results_setup,
                    results_teardown,
                    test['statusDetails'].get('trace') if
                    'statusDetails' in test and test['statusDetails'] else None,
                    attachments,
                    self.__form_parameters(test['parameters']) if 'parameters' in data_tests[
                        history_id] else None,
                    None,
                    links,
                    (int(test[f'{prefix}stop']) - int(
                        test[f'{prefix}start'])) if f'{prefix}stop' in test else 0,
                    None,
                    test['statusDetails']['message'] if
                    'statusDetails' in test and test[
                        'statusDetails'] and 'message' in test['statusDetails'] else None
                )
            )

    def __set_test_run(self):
        if self.__testrun_id is None:
            test_run_name = f'AllureRun {datetime.today().strftime("%d %b %Y %H:%M:%S")}'
            self.__testrun_id = self.__api_client.create_test_run(self.__project_id, test_run_name)

    def __send_attachments(self, attachments):
        ids = []

        if attachments:
            if 'attachment' in attachments:
                if type(attachments['attachment']) != list:
                    attachments = [attachments['attachment']]
                else:
                    attachments = attachments['attachment']

            prefix = '' if 'source' in attachments[0] else '@'

            for attachment in attachments:

                file = self.__parser.parse_attachment(f"{attachment[f'{prefix}source']}")

                if file is None:
                    continue

                attachment_id = self.__api_client.upload_attachment(file)

                if attachment_id:
                    ids.append({'id': attachment_id})

                self.__parser.clean_attachment(f"{attachment[f'{prefix}source']}")

        return ids

    def __get_data_from_labels(self, allure_labels):
        class_name = None
        namespace = None
        labels = []
        work_items_id = []

        if allure_labels:
            allure_labels, prefix = self.__parse_xml(allure_labels, 'label', 'value')

            for label in allure_labels:
                if label[f'{prefix}name'] == 'testcase':
                    work_items_id.append(label[f'{prefix}value'])
                else:
                    labels.append({'name': f"{label[f'{prefix}name']}::{label[f'{prefix}value']}"})

                if label[f'{prefix}name'] == 'package':
                    namespace = label[f'{prefix}value'].split('.')[-1]
                elif label[f'{prefix}name'] == 'parentSuite':
                    namespace = label[f'{prefix}value']
                elif label[f'{prefix}name'] in ('subSuite', 'suite'):
                    class_name = label[f'{prefix}value']
                elif label[f'{prefix}name'] == 'testClass':
                    class_name = label[f'{prefix}value'].split('.')[-1]

        return labels, namespace, class_name, work_items_id

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
            for link in allure_links:
                links.append({})

                if 'url' in link and re.fullmatch(
                        r'^(?:(?:(?:https?|ftp):)?\/\/)?(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-zA-Z0-9\u00a1-\uffff][a-zA-Z0-9\u00a1-\uffff_-]{0,62})?[a-zA-Z0-9\u00a1-\uffff]\.)+(?:[a-zA-Z\u00a1-\uffff]{2,}\.?))(?::\d{2,5})?(?:[/?#]\S*)?$',
                        link['url']):
                    links[-1]['url'] = link['url']
                else:
                    raise Exception('Some links have the wrong URL or no URL!')

                if 'type' in link and link['type'] in (
                        'Related', 'BlockedBy', 'Defect', 'Issue', 'Requirement', 'Repository'):
                    links[-1]['type'] = link['type']

                if 'name' in link:
                    links[-1]['title'] = link['name']

        return links

    def __form_steps(self, steps):
        adapt_steps = []
        results_steps = []

        if steps:
            steps, prefix = self.__parse_xml(steps, 'step', 'status')

            for step in steps:
                if 'name' in step:
                    if 'steps' in step:
                        inner_steps, inner_results_steps = self.__form_steps(step['steps'])
                    else:
                        inner_steps = []
                        inner_results_steps = []

                    adapt_steps.append(
                        {
                            'title': step['name'],
                            'steps': inner_steps
                        }
                    )

                    attachments = self.__send_attachments(step['attachments']) if 'attachments' in step else []

                    results_steps.append(
                        {
                            'title': step['name'],
                            'stepResults': inner_results_steps,
                            'outcome': step[f'{prefix}status'].title() if step[f'{prefix}status'] in (
                                'passed', 'skipped') else 'Failed',
                            'duration': (int(step[f'{prefix}stop']) - int(
                                step[f'{prefix}start'])) if f'{prefix}stop' in step else 0,
                            "attachments": attachments,
                            'parameters': self.__form_parameters(step['parameters']) if 'parameters' in step else None
                        }
                    )

        return adapt_steps, results_steps

    def __form_parameters(self, allure_parameters):
        parameters = {}

        if allure_parameters:
            allure_parameters, prefix = self.__parse_xml(allure_parameters, 'parameter', 'value')

            for parameter in allure_parameters:
                parameters[parameter[f'{prefix}name']] = parameter[f'{prefix}value']

        return parameters

    def __form_setup_teardown(self, data_before_after, test_uuid):
        setup = []
        teardown = []
        results_setup = []
        results_teardown = []

        if test_uuid:
            for uuid in data_before_after:
                if 'children' in data_before_after[uuid]:
                    for child in data_before_after[uuid]['children']:
                        if child == test_uuid:
                            steps, results_steps = self.__form_steps(data_before_after[uuid].get('befores'))
                            setup += steps
                            results_setup += results_steps
                            steps, results_steps = self.__form_steps(data_before_after[uuid].get('afters'))
                            teardown += steps
                            results_teardown += results_steps

        return setup, results_setup, teardown, results_teardown
