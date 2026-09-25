import unittest
from unittest.mock import MagicMock

from adapters_api.model.attachment_put_model import AttachmentPutModel

from testit_importer_allure.importer import Importer
from testit_importer_allure.models import LinkType, TestResult
from testit_importer_allure.models.status_type import StatusType


def _config(
        project_id='project-1',
        configuration_id='config-1',
        testrun=None,
        testrun_name=None,
        ignore_package_name=False,
        include_reruns=False,
        path='/results',
        tags=None,
        links=None):
    config = MagicMock()
    config.get_project_id.return_value = project_id
    config.get_configuration_id.return_value = configuration_id
    config.specified_testrun = testrun
    config.specified_testrun_name = testrun_name
    config.get_ignore_package_name.return_value = ignore_package_name
    config.get_include_reruns.return_value = include_reruns
    config.get_path.return_value = path
    config.get_test_run_tags.return_value = tags
    config.get_test_run_links.return_value = links
    return config


def _importer(api_client=None, parser=None, **config_kwargs) -> Importer:
    if parser is None:
        parser = MagicMock()
        parser.get_error_count.return_value = 0
    api_client = api_client or MagicMock()
    return Importer(parser, api_client, _config(**config_kwargs))


class ImporterLogicTests(unittest.TestCase):
    def test_parse_status_type(self):
        importer = _importer()

        self.assertEqual(
            importer._Importer__parse_status_type({}, ''),
            StatusType.INCOMPLETE)
        self.assertEqual(
            importer._Importer__parse_status_type({'status': 'skipped'}, ''),
            StatusType.INCOMPLETE)
        self.assertEqual(
            importer._Importer__parse_status_type({'status': 'passed'}, ''),
            StatusType.SUCCEEDED)
        self.assertEqual(
            importer._Importer__parse_status_type({'status': 'failed'}, ''),
            StatusType.FAILED)
        self.assertEqual(
            importer._Importer__parse_status_type({'@status': 'broken'}, '@'),
            StatusType.FAILED)

    def test_get_description(self):
        importer = _importer()

        self.assertEqual(importer._Importer__get_description('plain'), 'plain')
        self.assertEqual(importer._Importer__get_description({'#text': 'xml'}), 'xml')
        self.assertIsNone(importer._Importer__get_description({'other': 'x'}))
        self.assertIsNone(importer._Importer__get_description(None))

    def test_get_main_suites_parent_and_suite(self):
        importer = _importer()
        suites = importer._Importer__get_main_suites({
            'parentSuite': 'Root',
            'suite': 'Child',
            'package': 'com.example.pkg',
        })
        self.assertEqual(suites, ['Root', 'Child'])

    def test_get_main_suites_ignore_package_stops_after_parent(self):
        importer = _importer(ignore_package_name=True)
        suites = importer._Importer__get_main_suites({
            'parentSuite': 'Root',
            'suite': 'Child',
            'package': 'com.example.pkg',
        })
        self.assertEqual(suites, ['Root'])

    def test_get_main_suites_falls_back_to_last_package_part(self):
        importer = _importer()
        suites = importer._Importer__get_main_suites({'package': 'com.example.pkg.'})
        self.assertEqual(suites, ['pkg'])

    def test_get_sub_suite_prefers_sub_suite(self):
        importer = _importer()
        self.assertEqual(
            importer._Importer__get_sub_suite({'subSuite': 'Sub', 'testClass': 'a.b.C'}),
            'Sub')
        self.assertEqual(
            importer._Importer__get_sub_suite({'testClass': 'a.b.MyClass'}),
            'MyClass')
        self.assertIsNone(importer._Importer__get_sub_suite({}))

    def test_set_data_from_labels_extracts_work_items_and_namespace(self):
        importer = _importer()
        test_result = TestResult()

        labels = {
            'label': [
                {'name': 'testcase', 'value': 'WI-1'},
                {'name': 'parentSuite', 'value': 'Root'},
                {'name': 'suite', 'value': 'Child'},
                {'name': 'subSuite', 'value': 'Sub'},
                {'name': 'severity', 'value': 'smoke'},
            ]
        }

        importer._Importer__set_data_from_labels(test_result, labels)

        self.assertEqual(test_result.get_work_item_ids(), ['WI-1'])
        self.assertEqual(test_result.get_namespace(), 'Root.Child')
        self.assertEqual(test_result.get_classname(), 'Sub')
        self.assertEqual(len(test_result.get_labels()), 4)
        self.assertTrue(any(label.name == 'severity::smoke' for label in test_result.get_labels()))

    def test_form_links_valid(self):
        importer = _importer()
        links = importer._Importer__form_links([
            {'url': 'https://example.com/path', 'name': 'doc', 'type': 'issue'},
            {'url': 'https://repo.example/x', 'type': 'repository'},
        ])

        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].get_url(), 'https://example.com/path')
        self.assertEqual(links[0].get_title(), 'doc')
        self.assertEqual(links[0].get_link_type(), LinkType.ISSUE)
        self.assertEqual(links[1].get_link_type(), LinkType.REPOSITORY)

    def test_form_links_invalid_url_raises(self):
        importer = _importer()
        with self.assertRaises(Exception) as ctx:
            importer._Importer__form_links([{'url': 'not-a-url', 'name': 'bad'}])
        self.assertIn('wrong URL', str(ctx.exception))

    def test_parse_xml_unwraps_list_and_single(self):
        importer = _importer()

        multi, prefix = importer._Importer__parse_xml(
            {'label': [{'name': 'a', 'value': '1'}, {'name': 'b', 'value': '2'}]},
            'label',
            'value')
        self.assertEqual(prefix, '')
        self.assertEqual(len(multi), 2)

        single, prefix = importer._Importer__parse_xml(
            {'label': {'@name': 'a', '@value': '1'}},
            'label',
            'value')
        self.assertEqual(prefix, '@')
        self.assertEqual(len(single), 1)

    def test_form_parameters(self):
        importer = _importer()
        params = importer._Importer__form_parameters({
            'parameter': [
                {'name': 'browser', 'value': 'chrome'},
                {'name': 'empty'},
                None,
            ]
        })
        self.assertEqual(params, {'browser': 'chrome', 'empty': ''})

    def test_form_steps_sorts_and_maps_outcomes(self):
        importer = _importer()
        importer._Importer__send_attachments = MagicMock(return_value=[])

        steps = importer._Importer__form_steps({
            'step': [
                {'name': 'second', 'status': 'failed', 'start': '2000', 'stop': '2500'},
                {'name': 'first', 'status': 'passed', 'start': '1000', 'stop': '1500'},
                {'start': '500', 'stop': '600'},  # skipped: no name
            ]
        })

        self.assertEqual([s.get_title() for s in steps], ['first', 'second'])
        self.assertEqual(steps[0].get_outcome(), 'Passed')
        self.assertEqual(steps[1].get_outcome(), 'Failed')
        self.assertEqual(steps[0].get_duration(), 500)

    def test_form_fixtures_and_setup_teardown_order(self):
        importer = _importer()
        step_a = MagicMock(name='before-a')
        step_b = MagicMock(name='before-b')
        after_a = MagicMock(name='after-a')
        after_b = MagicMock(name='after-b')

        importer._Importer__form_steps = MagicMock(side_effect=[
            [step_a], [after_a],
            [step_b], [after_b],
        ])

        fixtures = importer._Importer__form_fixtures({
            'c1': {'start': '1000', 'children': ['t1'], 'befores': {'x': 1}, 'afters': {'y': 1}},
            'c2': {'start': '2000', 'children': ['t1'], 'befores': {'x': 2}, 'afters': {'y': 2}},
            'skip': {'children': ['t1']},  # no start
        })

        self.assertEqual(len(fixtures['t1']), 2)

        test_result = MagicMock()
        chain = test_result.set_setup_results.return_value
        importer._Importer__form_setup_teardown(test_result, fixtures, 't1', '')

        test_result.set_setup_results.assert_called_once_with([step_a, step_b])
        chain.set_teardown_results.assert_called_once_with([after_b, after_a])

    def test_form_test_result_json_shape(self):
        importer = _importer()
        importer._Importer__send_attachments = MagicMock(
            return_value=[AttachmentPutModel(id='att-1')])
        importer._Importer__form_setup_teardown = MagicMock()

        test = {
            'uuid': 'u-1',
            'fullName': 'com.example.Test',
            'start': '1000000',
            'stop': '1001500',
            'status': 'passed',
            'labels': {'label': [{'name': 'suite', 'value': 'S1'}]},
            'attachments': {'attachment': [{'source': 'a.png'}]},
            'links': [{'url': 'https://example.com', 'name': 'L'}],
            'statusDetails': {'trace': 'trace', 'message': 'msg'},
            'parameters': {'parameter': [{'name': 'p', 'value': '1'}]},
            'steps': {'step': [{'name': 's', 'status': 'passed', 'start': '1000000', 'stop': '1000100'}]},
        }

        result = importer._Importer__form_test_result(test, {}, 'hist-1')

        self.assertEqual(result.get_external_id(), 'hist-1')
        self.assertEqual(result.get_title(), 'com.example.Test')
        self.assertEqual(result.get_outcome(), 'passed')
        self.assertEqual(result.get_status_type(), StatusType.SUCCEEDED)
        self.assertEqual(result.get_duration(), 1500)
        self.assertEqual(result.get_message(), 'msg')
        self.assertEqual(result.get_traces(), 'trace')
        self.assertEqual(result.get_parameters(), {'p': '1'})
        self.assertEqual(len(result.get_attachments()), 1)
        self.assertEqual(result.get_namespace(), 'S1')
        self.assertEqual(len(result.get_step_results()), 1)

    def test_set_test_run_uses_existing_id(self):
        api = MagicMock()
        importer = _importer(api_client=api, testrun='run-1', tags=['t'], links=[{'url': 'https://a'}])

        importer._Importer__set_test_run()

        api.apply_test_run_tags_and_links.assert_called_once_with(
            'run-1', ['t'], [{'url': 'https://a'}])
        api.create_test_run.assert_not_called()

    def test_set_test_run_creates_with_custom_name(self):
        api = MagicMock()
        api.create_test_run.return_value = 'new-run'
        importer = _importer(api_client=api, testrun_name='Nightly')

        importer._Importer__set_test_run()

        args = api.create_test_run.call_args[0]
        self.assertEqual(args[0], 'project-1')
        self.assertTrue(args[1].startswith('Nightly '))
        self.assertEqual(importer._Importer__testrun_id, 'new-run')

    def test_set_test_run_default_name(self):
        api = MagicMock()
        api.create_test_run.return_value = 'new-run'
        importer = _importer(api_client=api)

        importer._Importer__set_test_run()

        self.assertTrue(api.create_test_run.call_args[0][1].startswith('AllureRun '))

    def test_send_test_result_creates_when_missing(self):
        api = MagicMock()
        api.get_autotest.return_value = []
        api.create_autotest.return_value = 'at-1'
        importer = _importer(api_client=api, testrun='run-1')
        formed = (
            TestResult()
            .set_external_id('ext')
            .set_title('name')
            .set_outcome('passed')
            .set_status_type(StatusType.SUCCEEDED)
            .set_work_item_ids(['WI-1'])
            .set_step_results([])
            .set_setup_results([])
            .set_teardown_results([])
            .set_links([])
            .set_labels([])
            .set_attachments([])
            .set_parameters({})
            .set_duration(0)
        )
        importer._Importer__form_test_result = MagicMock(return_value=formed)

        importer._Importer__send_test_result({'uuid': 'u'}, {}, 'hist', ['PASSED'])

        api.create_autotest.assert_called_once()
        api.update_autotest.assert_not_called()
        api.link_autotest.assert_called_once_with('at-1', 'WI-1')
        api.send_test_result.assert_called_once()
        self.assertEqual(api.send_test_result.call_args[0][0], 'run-1')

    def test_send_test_result_updates_existing(self):
        api = MagicMock()
        existing = MagicMock(id='at-2', is_flaky=True)
        api.get_autotest.return_value = [existing]
        importer = _importer(api_client=api, testrun='run-1')
        formed = (
            TestResult()
            .set_external_id('ext')
            .set_title('name')
            .set_outcome('passed')
            .set_status_type(StatusType.SUCCEEDED)
            .set_work_item_ids([])
            .set_step_results([])
            .set_setup_results([])
            .set_teardown_results([])
            .set_links([])
            .set_labels([])
            .set_attachments([])
            .set_parameters({})
            .set_duration(0)
        )
        importer._Importer__form_test_result = MagicMock(return_value=formed)

        importer._Importer__send_test_result({'uuid': 'u'}, {}, 'hist', [])

        self.assertTrue(formed.get_is_flaky())
        api.update_autotest.assert_called_once()
        api.create_autotest.assert_not_called()

    def test_send_result_sends_only_last_without_reruns(self):
        api = MagicMock()
        api.get_status_codes.return_value = []
        parser = MagicMock()
        parser.get_error_count.return_value = 0
        parser.parse_results.return_value = (
            {
                'h1': [
                    {'uuid': '1', 'start': '1000'},
                    {'uuid': '2', 'start': '2000'},
                ]
            },
            {},
        )
        importer = _importer(api_client=api, parser=parser, testrun='run-1', include_reruns=False)
        importer._Importer__form_fixtures = MagicMock(return_value={})
        importer._Importer__send_test_result = MagicMock()

        errors = importer.send_result()

        self.assertEqual(errors, 0)
        importer._Importer__send_test_result.assert_called_once()
        sent_test = importer._Importer__send_test_result.call_args[0][0]
        self.assertEqual(sent_test['uuid'], '2')

    def test_send_result_sends_all_with_reruns(self):
        api = MagicMock()
        api.get_status_codes.return_value = []
        parser = MagicMock()
        parser.get_error_count.return_value = 0
        parser.parse_results.return_value = (
            {
                'h1': [
                    {'uuid': '1', 'start': '1000'},
                    {'uuid': '2', 'start': '2000'},
                ]
            },
            {},
        )
        importer = _importer(api_client=api, parser=parser, testrun='run-1', include_reruns=True)
        importer._Importer__form_fixtures = MagicMock(return_value={})
        importer._Importer__send_test_result = MagicMock()

        importer.send_result()

        self.assertEqual(importer._Importer__send_test_result.call_count, 2)

    def test_send_result_counts_prepare_and_send_errors(self):
        api = MagicMock()
        api.get_status_codes.return_value = []
        parser = MagicMock()
        parser.get_error_count.return_value = 1
        parser.parse_results.return_value = (
            {
                'h1': [
                    {'uuid': 'bad'},  # no start -> prepare error
                    {'uuid': 'ok', 'start': '1000'},
                ]
            },
            {},
        )
        importer = _importer(api_client=api, parser=parser, testrun='run-1')
        importer._Importer__form_fixtures = MagicMock(return_value={})
        importer._Importer__send_test_result = MagicMock(side_effect=RuntimeError('boom'))

        errors = importer.send_result()

        self.assertEqual(errors, 3)  # parser(1) + prepare(1) + send(1)


if __name__ == '__main__':
    unittest.main()
