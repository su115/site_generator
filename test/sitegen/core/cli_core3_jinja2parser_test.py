from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

from sitegen.core.cli_core3 import Jinja2Parser, StrictUndefined

PATH = "sitegen.core.cli_core3"


class Jinja2ParserTest(TestCase):
    @patch(PATH + ".SchemaValidator")
    def test__validate_block(self, sc_mock):
        block_dir = MagicMock()
        jp = Jinja2Parser(block_dir)
        block = Mock(block_name="b1_name")
        block.content.get_content_dict.return_value = "content"
        block_dir.__truediv__.return_value.__truediv__.return_value = "schema_path"

        jp._validate_block(block)

        sc_mock.assert_called_once_with(3)
        sc_mock.return_value.verify_json_by_path.assert_called_once_with("schema_path", "content")

    @patch(PATH + ".FileSystemLoader")
    @patch(PATH + ".Environment")
    def test__get_template(self, mock_env, mock_fsl):
        jp = Jinja2Parser("block_dir")
        block = Mock(block_name="block_name")
        mock_env.return_value.globals = {}
        expected_env = {"raise": RuntimeError}

        result = jp._get_template(block)

        mock_fsl.assert_called_once_with("block_dir")
        mock_env.assert_called_once_with(
            loader=mock_fsl.return_value,
            undefined=StrictUndefined,
            autoescape=False,
        )
        self.assertEqual(expected_env, mock_env.return_value.globals)
        self.assertEqual(mock_env.return_value.get_template.return_value, result)
        mock_env.return_value.get_template.assert_called_once_with("block_name/base.j2")

    @patch(PATH + ".Jinja2Parser._validate_block")
    @patch(PATH + ".Jinja2Parser._get_template")
    @patch(PATH + ".Jinja2Parser._split_content")
    def test_parse_block(self, mock_spl, mock_gt, mock_val):
        jp = Jinja2Parser("block_dir")
        block = Mock(block_name="b1", content="block_cont")
        template = mock_gt.return_value

        result = jp.parse_block(block, "test", inline_blocks={"some": "staff"})

        mock_val.assert_called_once_with(block)
        mock_gt.assert_called_once_with(block)
        template.render.assert_called_once_with(content="block_cont", site_name="test", inline_blocks={"some": "staff"})
        mock_spl.assert_called_once_with("b1", template.render.return_value)
        self.assertEqual(mock_spl.return_value, result)

    def test__split_content_slit(self):
        data = "data1\n<!-- SPLIT -->\ndata2"
        expected = {"block_1_part1": "data1\n", "block_1_part2": "\ndata2"}
        jp = Jinja2Parser("block_dir")

        result = jp._split_content("block_1", data)

        self.assertEqual(expected, result)

    def test__split_content_not_slit(self):
        data = "data1\ndata2"
        expected = {"block_1": data}
        jp = Jinja2Parser("block_dir")

        result = jp._split_content("block_1", data)

        self.assertEqual(expected, result)
