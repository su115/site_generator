import json
from unittest import TestCase
from unittest.mock import MagicMock, Mock, call, patch

from sitegen.core.cli_core3 import Collector

PATH = "sitegen.core.cli_core3"


raw_block_record = """{
    "block_name":"test",
    "content_type":"common",
    "content_lang":"common",
    "content": {},
    "inline_blocks": []
}"""


class BlocksCollectorTest(TestCase):
    def setUp(self):
        self.json_dir = Mock()
        self.json_file = Mock()
        self.json_dir.glob.return_value = [self.json_file]
        raw_data = "[" + raw_block_record + "]"
        self.json_file.read_text.return_value = raw_data

    def test_collecting(self):
        expected = json.loads(raw_block_record)

        result = Collector.collect_blocks(self.json_dir)

        self.assertEqual(expected, result[0].get_content_dict())
        self.json_dir.glob.assert_called_once_with("*.json")
        self.json_file.read_text.assert_called_once_with(encoding="utf-8")

    def test_raw_json_data_is_list(self):
        self.json_file.read_text.return_value = raw_block_record

        with self.assertRaises(TypeError):
            Collector.collect_blocks(self.json_dir)

    def test_raw_json_data_is_dict_in_list(self):
        self.json_file.read_text.return_value = "[ true ]"

        with self.assertRaises(TypeError):
            Collector.collect_blocks(self.json_dir)


def get_asset_content(block_dir, block_name, file):
    return file


class AssetsCollectorTest(TestCase):
    @patch(PATH + ".Collector._get_asset_content", side_effect=get_asset_content)
    def test_collection(self, get_asset_mock):
        calls = [call("block_dir", "b1", "base.css"), call("block_dir", "b1", "base.js")]
        expected = {"block_css": "base.css", "block_js": "base.js"}

        result = Collector.collect_assets([Mock(block_name="b1")], "block_dir")

        get_asset_mock.assert_has_calls(calls)
        self.assertEqual(expected, result)

    def test__get_asset_content_empty(self):
        expected = ""
        block_dir = MagicMock()
        answer = Mock()
        answer.exists.return_value = False
        block_dir.__truediv__.return_value.__truediv__.return_value = answer

        result = Collector._get_asset_content(block_dir, "b1", "file.json")

        self.assertEqual(expected, result)

    def test__get_asset_content(self):
        expected = "\nsome data"
        block_dir = MagicMock()
        answer = Mock()
        answer.exists.return_value = True
        answer.read_text.return_value = "some data"
        block_dir.__truediv__.return_value.__truediv__.return_value = answer

        result = Collector._get_asset_content(block_dir, "b1", "file.json")

        self.assertEqual(expected, result)
