from unittest import TestCase

from app.parsers.jobs import JobParser


class TestParserClass(TestCase):

    SETTINGS_FILE_NAME = 'settings.json'

    def test_settings(self):
        parser_class = JobParser(self.SETTINGS_FILE_NAME)
        settings_json = parser_class._read_settings(self.SETTINGS_FILE_NAME)
        self.assertTrue('url' in settings_json.keys())

    def test_parse_page(self):
        parser_class = JobParser(self.SETTINGS_FILE_NAME)
        PAGE_NUMBER = 10
        actual = parser_class._parse_page(PAGE_NUMBER)
        self.assertLess(0, actual.shape[0])

    def test_parse(self):
        parser_class = JobParser(self.SETTINGS_FILE_NAME)
        actual = parser_class.parse()
        pass