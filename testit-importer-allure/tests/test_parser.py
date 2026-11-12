import io
import json
import unittest
from typing import Dict, List

from testit_importer_allure.filedto import FileDto
from testit_importer_allure.parser import Parser


class _FakeReader:
    def __init__(self, files: Dict[str, object]):
        self._files = files

    def get_all_files(self) -> List[str]:
        return list(self._files.keys())

    def read_file(self, file_path: str) -> FileDto:
        payload = self._files[file_path]
        if isinstance(payload, (dict, list)):
            content = json.dumps(payload).encode('utf-8')
        elif isinstance(payload, str):
            content = payload.encode('utf-8')
        else:
            content = payload
        return FileDto(file_path, io.BytesIO(content))

    def read_attachment(self, file_name: str):
        raise NotImplementedError

    def remove_attachment(self, file_name: str) -> None:
        pass


class ParserJsonFilterTests(unittest.TestCase):
    def test_parses_result_and_container_skips_service_and_attachment(self):
        reader = _FakeReader({
            'a1b2c3d4-result.json': {
                'uuid': 'a1b2c3d4',
                'historyId': 'hist-1',
                'name': 'My test',
                'status': 'passed',
            },
            'cont-1-container.json': {
                'uuid': 'cont-1',
                'children': ['a1b2c3d4'],
            },
            'executor.json': {
                'name': 'Jenkins',
                'type': 'jenkins',
                'buildName': 'job#1',
            },
            'environment.json': [{'name': 'browser', 'value': 'chrome'}],
            'categories.json': [{'name': 'Product defects'}],
            '8d800d1e-52cc-495f-bc9b-80ea156ee4b2-attachment.json': ['row1', 'row2'],
            'note.txt': 'ignored by extension',
        })
        parser = Parser(reader, use_name=False)

        data_tests, data_containers = parser.parse_results()

        self.assertEqual(list(data_tests.keys()), ['hist-1'])
        self.assertEqual(len(data_tests['hist-1']), 1)
        self.assertEqual(data_tests['hist-1'][0]['uuid'], 'a1b2c3d4')
        self.assertEqual(list(data_containers.keys()), ['cont-1'])
        self.assertEqual(parser.get_error_count(), 0)

    def test_result_without_history_uses_uuid_hash(self):
        reader = _FakeReader({
            'uuid-1-result.json': {
                'uuid': 'uuid-1',
                'name': 'No history',
                'status': 'passed',
            },
        })
        parser = Parser(reader, use_name=False)

        data_tests, _ = parser.parse_results()

        self.assertEqual(len(data_tests), 1)
        self.assertEqual(parser.get_error_count(), 0)

    def test_minio_style_path_suffix_still_matches(self):
        reader = _FakeReader({
            'run/prefix/uuid-2-result.json': {
                'uuid': 'uuid-2',
                'historyId': 'hist-2',
                'name': 'Nested',
                'status': 'passed',
            },
            'run/prefix/executor.json': {'name': 'CI'},
        })
        parser = Parser(reader, use_name=False)

        data_tests, _ = parser.parse_results()

        self.assertEqual(list(data_tests.keys()), ['hist-2'])
        self.assertEqual(parser.get_error_count(), 0)


if __name__ == '__main__':
    unittest.main()
