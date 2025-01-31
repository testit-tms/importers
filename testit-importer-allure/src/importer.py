"""The module provides functionality for importing result to TMS"""
import re
import dataclasses
from datetime import datetime
from .apiclient import ApiClient
from .configurator import Configurator
from .parser import Parser
from .converter import Converter


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

    def send_result(self):
        """Function imports result to TMS."""
        data_tests, data_fixtures = self.__parser.parse_results()

        self.__set_test_run()

        for history_id in data_tests:

            test = data_tests[history_id]
            prefix = '' if 'uuid' in test else '@'

            if 'name' not in test and 'fullName' in test:
                test['name'] = test['fullName']

            if 'labels' in test:
                test['labels'], test['namespace'], test['classname'], work_items_id = \
                    self.__get_data_from_labels(test['labels'])
            else:
                test['labels'] = []
                test['namespace'] = None
                test['classname'] = None
                work_items_id = []

            test['external_id'] = history_id
            test['attachments'] = self.__send_attachments(test['attachments']) if 'attachments' in test else []
            test['setup'], test['setup_results'], test['teardown'], test['teardown_results'] = \
                self.__form_setup_teardown(data_fixtures, test.get('uuid', None))
            test['steps'], test['step_results'] = self.__form_steps(test.get('steps', None))
            test['links'] = self.__form_links(test['links']) if 'links' in test else []
            test['traces'] = test['statusDetails'].get('trace') if \
                'statusDetails' in test and test['statusDetails'] else None
            test['message'] = test['statusDetails']['message'] if \
                'statusDetails' in test and test['statusDetails'] and 'message' in test['statusDetails'] else None
            test['parameters'] = self.__form_parameters(test['parameters']) if 'parameters' in test else None
            test['duration'] = (int(test[f'{prefix}stop']) - int(test[f'{prefix}start'])) if \
                f'{prefix}stop' in test else 0
            test['started_on'] = datetime.fromtimestamp(int(test[f'{prefix}start']) / 1000.0)
            test['completed_on'] = datetime.fromtimestamp(int(test[f'{prefix}stop']) / 1000.0)
            test['description'] = self.__get_description(test.get('description', None))

            if f'{prefix}status' in test:
                test['outcome'] = \
                    test[f'{prefix}status'].title() if test[f'{prefix}status'] in ('passed', 'skipped') else 'Failed'
            else:
                test['outcome'] = 'Blocked'

            autotest = self.__api_client.get_autotest(
                Converter.project_id_and_external_id_to_autotests_select_model(self.__project_id, history_id)
            )

            if not autotest:
                autotest_id = self.__api_client.create_autotest(
                    Converter.test_result_to_autotest_post_model(test, self.__project_id)
                )
            else:
                autotest_id = autotest[0].id

                if test['outcome'] == 'Passed':
                    test['is_flaky'] = autotest[0].is_flaky

                    self.__api_client.update_autotest(
                        Converter.test_result_to_autotest_put_model(test, self.__project_id)
                    )
                else:
                    autotest[0].links = Converter.links_to_links_put_model(test['links'])

                    for i in range(0, len(autotest[0].labels)):
                        autotest[0].labels[i] = \
                            Converter.label_to_label_post_model(autotest[0].labels[i].name)

                    self.__api_client.update_autotest(
                        Converter.auto_test_model_to_update_autotest_put_model(autotest[0], self.__project_id)
                    )

            for work_item_id in work_items_id:
                self.__api_client.link_autotest(autotest_id, work_item_id)

            self.__api_client.send_test_result(
                self.__testrun_id,
                Converter.test_result_to_testrun_result_post_model(test, self.__configuration_id)
            )

    def __set_test_run(self):
        if self.__testrun_id is None:
            if self.__testrun_name is not None:
                test_run_name = f'{self.__testrun_name} {datetime.today().strftime("%d %b %Y %H:%M:%S")}'
            else:
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
                    ids.append(attachment_id)

                self.__parser.clean_attachment(f"{attachment[f'{prefix}source']}")

        return ids

    @staticmethod
    def __get_description(allure_description):
        if type(allure_description) == 'str':
            return allure_description
        elif type(allure_description) == 'dict':
            return allure_description.get('#text', None)

        return None

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
                    labels.append(
                        Converter.label_to_label_post_model(
                            f"{label[f'{prefix}name']}::{label[f'{prefix}value']}"))

                if label[f'{prefix}name'] == 'package' and not self.__ignore_namespace_name:
                    packages = label[f'{prefix}value'].split('.')

                    while packages and not packages[-1]:
                        del packages[-1]

                    if packages:
                        namespace = packages[-1]
                elif label[f'{prefix}name'] == 'parentSuite' and label[f'{prefix}value']:
                    namespace = label[f'{prefix}value']
                elif label[f'{prefix}name'] in ('subSuite', 'suite') and label[f'{prefix}value']:
                    class_name = label[f'{prefix}value']
                elif label[f'{prefix}name'] == 'testClass' and label[f'{prefix}value'].split('.')[-1]:
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
                        r'^(?:(?:(?:https?|ftp):)?\/\/)?(?:(?:[1-9]\d?|1\d\d|2[01]\d|22[0-3])(?:\.(?:1?\d{1,2}|2[0-4]\d|25[0-5])){2}(?:\.(?:[1-9]\d?|1\d\d|2[0-4]\d|25[0-4]))|(?:(?:[a-zA-Z0-9\u00a1-\uffff][a-zA-Z0-9\u00a1-\uffff_-]{0,62})?[a-zA-Z0-9\u00a1-\uffff]\.?)+(?:[a-zA-Z\u00a1-\uffff]{2,}\.?))(?::\d{2,5})?(?:[/?#]\S*)?$',
                        link['url']):
                    links[-1]['url'] = link['url']
                else:
                    raise Exception('Some links have the wrong URL or no URL!')

                if 'type' in link and link['type'].title() in (
                        'Related', 'BlockedBy', 'Defect', 'Issue', 'Requirement', 'Repository'):
                    links[-1]['type'] = link['type'].title()

                if 'name' in link:
                    links[-1]['title'] = str(link['name'])

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
                            'step_results': inner_results_steps,
                            'outcome': step[f'{prefix}status'].title() if f'{prefix}status' in step and step[f'{prefix}status'] in (
                                    'passed', 'skipped') else 'Failed',
                            'duration': (int(step[f'{prefix}stop']) - int(
                                step[f'{prefix}start'])) if f'{prefix}stop' in step else 0,
                            'started_on': datetime.fromtimestamp(
                                int(step[f'{prefix}start']) / 1000.0) if f'{prefix}start' in step else None,
                            'completed_on': datetime.fromtimestamp(
                                int(step[f'{prefix}stop']) / 1000.0) if f'{prefix}stop' in step else None,
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
                if parameter is None:
                    continue

                parameters[parameter[f'{prefix}name']] = str(parameter[f'{prefix}value']) if f'{prefix}value' in parameter else ''

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
