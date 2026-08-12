import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from test_run_meta import merge_links, merge_tags, parse_links, parse_tags  # noqa: E402


class TestRunMetaTests(unittest.TestCase):
    def test_parse_tags_comma_separated(self):
        self.assertEqual(parse_tags('smoke, nightly'), ['smoke', 'nightly'])

    def test_parse_tags_json_array(self):
        self.assertEqual(parse_tags('["smoke", "nightly"]'), ['smoke', 'nightly'])

    def test_parse_tags_empty(self):
        self.assertIsNone(parse_tags(None))
        self.assertIsNone(parse_tags(''))
        self.assertIsNone(parse_tags('   '))

    def test_parse_tags_invalid_json(self):
        self.assertIsNone(parse_tags('[smoke'))

    def test_parse_links_valid(self):
        raw = '[{"url":"https://ci.example/jobs/1","title":"CI Job","type":"Related"}]'
        self.assertEqual(
            parse_links(raw),
            [{'url': 'https://ci.example/jobs/1', 'title': 'CI Job', 'type': 'Related'}],
        )

    def test_parse_links_skips_without_url(self):
        self.assertIsNone(parse_links('[{"title":"no url"}]'))

    def test_parse_links_invalid_json(self):
        self.assertIsNone(parse_links('{not-json'))

    def test_merge_tags_preserves_existing(self):
        self.assertEqual(merge_tags(['smoke'], ['nightly', 'smoke']), ['smoke', 'nightly'])

    def test_merge_links_by_url(self):
        existing = [{'url': 'https://a', 'title': 'A'}]
        new = [{'url': 'https://a', 'title': 'dup'}, {'url': 'https://b', 'title': 'B'}]
        self.assertEqual(
            merge_links(existing, new),
            [{'url': 'https://a', 'title': 'A'}, {'url': 'https://b', 'title': 'B'}],
        )


if __name__ == '__main__':
    unittest.main()
