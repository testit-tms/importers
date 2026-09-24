import unittest

from datetime import datetime

from adapters_api.model.adapters_auto_tests_post_request import AdaptersAutoTestsPostRequest
from adapters_api.model.adapters_auto_tests_put_request import AdaptersAutoTestsPutRequest
from adapters_api.model.adapters_auto_tests_search_post_request import (
    AdaptersAutoTestsSearchPostRequest,
)
from adapters_api.model.auto_test_results_for_test_run_model import AutoTestResultsForTestRunModel
from adapters_api.model.link_create_api_model import LinkCreateApiModel
from adapters_api.model.link_post_model import LinkPostModel
from adapters_api.model.link_update_api_model import LinkUpdateApiModel

from testit_importer_allure.converter import Converter
from testit_importer_allure.models import Link, StepResult, TestResult
from testit_importer_allure.models.status_type import StatusType


def _test_result(**overrides) -> TestResult:
    result = TestResult()
    result.set_external_id(overrides.get('external_id', 'ext-1'))
    result.set_title(overrides.get('title', 'My test'))
    result.set_outcome(overrides.get('outcome', 'passed'))
    result.set_status_type(overrides.get('status_type', StatusType.SUCCEEDED))
    result.set_namespace(overrides.get('namespace', 'suite'))
    result.set_classname(overrides.get('classname', 'MyClass'))
    result.set_description(overrides.get('description', 'desc'))
    result.set_duration(overrides.get('duration', 1500.4))
    result.set_step_results(overrides.get('step_results', []))
    result.set_setup_results(overrides.get('setup_results', []))
    result.set_teardown_results(overrides.get('teardown_results', []))
    result.set_links(overrides.get('links', []))
    result.set_labels(overrides.get('labels', []))
    result.set_attachments(overrides.get('attachments', []))
    result.set_parameters(overrides.get('parameters', {}))
    result.set_is_flaky(overrides.get('is_flaky', False))
    result.set_message(overrides.get('message'))
    result.set_traces(overrides.get('traces'))
    result.set_started_on(overrides.get('started_on'))
    result.set_completed_on(overrides.get('completed_on'))
    return result


class ConverterTests(unittest.TestCase):
    def test_build_autotests_search_post_request(self):
        request = Converter.build_autotests_search_post_request('project-1', 'ext-1')

        self.assertIsInstance(request, AdaptersAutoTestsSearchPostRequest)
        self.assertEqual(request.filter.project_ids, ['project-1'])
        self.assertEqual(request.filter.external_ids, ['ext-1'])
        self.assertFalse(request.filter.is_deleted)
        self.assertFalse(request.includes.include_steps)
        self.assertFalse(request.includes.include_links)
        self.assertFalse(request.includes.include_labels)

    def test_test_result_to_create_autotest_request(self):
        link = Link().set_url('https://example.com').set_title('doc').set_link_type('Related')
        result = _test_result(links=[link], labels=[Converter.label_to_label_post_model('a::b')])

        model = Converter.test_result_to_create_autotest_request(result, 'project-1')

        self.assertIsInstance(model, AdaptersAutoTestsPostRequest)
        self.assertEqual(model.external_id, 'ext-1')
        self.assertEqual(model.project_id, 'project-1')
        self.assertEqual(model.name, 'My test')
        self.assertEqual(model.namespace, 'suite')
        self.assertEqual(model.classname, 'MyClass')
        self.assertEqual(len(model.links), 1)
        self.assertIsInstance(model.links[0], LinkCreateApiModel)
        self.assertEqual(model.links[0].url, 'https://example.com')
        self.assertNotIn('hasInfo', model.links[0].to_dict())

    def test_test_result_to_update_autotest_request(self):
        result = _test_result(is_flaky=True)
        model = Converter.test_result_to_update_autotest_request(result, 'project-1')

        self.assertIsInstance(model, AdaptersAutoTestsPutRequest)
        self.assertEqual(model.external_id, 'ext-1')
        self.assertTrue(model.is_flaky)
        self.assertFalse(model.reset_layer)

    def test_test_result_to_testrun_result_sets_status_code_when_known(self):
        result = _test_result(outcome='custom_pass')
        model = Converter.test_result_to_testrun_result_post_model(
            result, 'config-1', ['CUSTOM_PASS', 'FAILED'])

        self.assertIsInstance(model, AutoTestResultsForTestRunModel)
        self.assertEqual(model.configuration_id, 'config-1')
        self.assertEqual(model.auto_test_external_id, 'ext-1')
        self.assertEqual(model.status_code, 'custom_pass')
        self.assertEqual(model.duration, 1500)

    def test_test_result_to_testrun_result_skips_unknown_status_code(self):
        result = _test_result(outcome='passed')
        model = Converter.test_result_to_testrun_result_post_model(result, 'config-1', ['FAILED'])

        self.assertNotIn('statusCode', model.to_dict())

    def test_links_to_post_model_keeps_has_info(self):
        link = Link().set_url('https://example.com').set_title('t')
        models = Converter.links_to_links_post_model([link])

        self.assertEqual(len(models), 1)
        self.assertIsInstance(models[0], LinkPostModel)
        self.assertTrue(models[0].has_info)
        self.assertEqual(str(models[0].type), 'Related')

    def test_links_to_put_model_without_has_info(self):
        link = Link().set_url('https://example.com').set_title('t').set_link_type('Issue')
        models = Converter.links_to_links_put_model([link])

        self.assertEqual(len(models), 1)
        self.assertIsInstance(models[0], LinkUpdateApiModel)
        self.assertEqual(models[0].url, 'https://example.com')
        self.assertNotIn('hasInfo', models[0].to_dict())

    def test_step_results_to_autotest_steps_model_nested(self):
        child = StepResult().set_title('child')
        parent = StepResult().set_title('parent').set_step_results([child])

        models = Converter.step_results_to_autotest_steps_model([parent])

        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].title, 'parent')
        self.assertEqual(len(models[0].steps), 1)
        self.assertEqual(models[0].steps[0].title, 'child')

    def test_step_results_to_attachment_put_model(self):
        started = datetime(2024, 1, 1, 12, 0, 0)
        completed = datetime(2024, 1, 1, 12, 0, 1)
        step = (
            StepResult()
            .set_title('step')
            .set_outcome('Passed')
            .set_duration(1000)
            .set_started_on(started)
            .set_completed_on(completed)
            .set_parameters({'a': '1'})
            .set_attachments([])
        )

        models = Converter.step_results_to_attachment_put_model_autotest_step_results_model([step])

        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].title, 'step')
        self.assertEqual(models[0].duration, 1000)
        self.assertEqual(models[0].parameters, {'a': '1'})

    def test_label_to_label_post_model(self):
        label = Converter.label_to_label_post_model('severity::value')
        self.assertEqual(label.name, 'severity::value')


if __name__ == '__main__':
    unittest.main()
