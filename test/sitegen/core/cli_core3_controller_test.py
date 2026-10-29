from pathlib import Path as RealPath
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

from sitegen.core.cli_core3 import Controller

PATH = "sitegen.core.cli_core3"


class ControllerLoadConfigTest(TestCase):
    @patch(PATH + ".Path")
    def test_config_not_found(self, mock_path):
        c = Controller()
        mock_path.return_value.exists.return_value = False

        with self.assertRaises(ValueError):
            c.load_config()

        mock_path.assert_called_once_with("sitegen.yaml")

    @patch(PATH + ".yaml.safe_load")
    @patch(PATH + ".SchemaValidator")
    @patch(PATH + ".Path")
    def test_load_config(self, mock_path, mock_SV, mock_ysl):
        def side_effect(arg):
            if arg == "sitegen.yaml":
                mock_config_file = Mock()
                mock_config_file.read_text.return_value = "some yaml data"
                mock_config_file.exists.return_value = True
                return mock_config_file
            return RealPath(arg)

        mock_path.side_effect = side_effect
        c = Controller()
        mock_ysl.return_value = {
            "block_entrypoint": "aa",
            "json_directory": "jj",
            "block_directory": "bb",
            "sites_directory": "ss",
            "sites": [{"name": "s1", "lang": "en"}, {"name": "s2", "lang": "ua"}],
        }
        expected_sites = [{"site_name": "s1", "lang": "en"}, {"site_name": "s2", "lang": "ua"}]

        result = c.load_config()

        mock_ysl.assert_called_once_with("some yaml data")
        mock_SV.assert_called_once_with(5)

        self.assertIs(c, result)
        self.assertEqual(expected_sites, c.sites)
        self.assertEqual("aa", c.entrypoint)
        self.assertEqual("jj", str(c.json_directory))
        self.assertEqual("bb", str(c.block_directory))
        self.assertEqual("ss", str(c.sites_directory))


class ControllerInitializeSkelTest(TestCase):
    @patch(PATH + ".Path")
    @patch(PATH + ".shutil")
    @patch(PATH + ".Controller.load_config")
    def test_config_exists(self, mock_load, mock_sh, mock_path):
        def side_effect(arg):
            if arg == "sitegen.yaml":
                mock_config_file = Mock()
                mock_config_file.is_file.return_value = True
                return mock_config_file
            return RealPath(arg)

        mock_path.side_effect = side_effect
        c = Controller()
        c.json_directory = Mock()
        c.block_directory = Mock()
        c.sites_directory = Mock()
        c.json_directory.exists.return_value = False
        c.block_directory.exists.return_value = False
        c.sites_directory.exists.return_value = False

        c.initialize_skeleton()

        mock_load.assert_called_once()
        c.json_directory.mkdir.assert_called_once_with(exist_ok=True, parents=True)
        c.block_directory.mkdir.assert_called_once_with(exist_ok=True, parents=True)
        c.sites_directory.mkdir.assert_called_once_with(exist_ok=True, parents=True)

        mock_sh.copytree.assert_called()

    @patch(PATH + ".Path")
    @patch(PATH + ".shutil")
    @patch(PATH + ".Controller.load_config")
    def test_config_not_exists(self, mock_load, mock_sh, mock_path):
        def side_effect(arg):
            if arg == "sitegen.yaml":
                mock_config_file = Mock()
                mock_config_file.is_file.return_value = False
                return mock_config_file
            return RealPath(arg)

        mock_path.side_effect = side_effect
        c = Controller()
        c.json_directory = Mock()
        c.block_directory = Mock()
        c.sites_directory = Mock()
        c.json_directory.exists.return_value = False
        c.block_directory.exists.return_value = False
        c.sites_directory.exists.return_value = False

        c.initialize_skeleton()

        mock_load.assert_called_once()
        c.json_directory.mkdir.assert_called_once_with(exist_ok=True, parents=True)
        c.block_directory.mkdir.assert_called_once_with(exist_ok=True, parents=True)
        c.sites_directory.mkdir.assert_called_once_with(exist_ok=True, parents=True)

        mock_sh.copytree.assert_called()
        mock_sh.copy.assert_called()

    @patch(PATH + ".Path")
    @patch(PATH + ".shutil")
    @patch(PATH + ".Controller.load_config")
    def test_environment_not_clean(self, mock_load, mock_sh, mock_path):
        def side_effect(arg):
            if arg == "sitegen.yaml":
                mock_config_file = Mock()
                mock_config_file.is_file.return_value = True
                return mock_config_file
            return RealPath(arg)

        mock_path.side_effect = side_effect
        c = Controller()
        c.json_directory = Mock()
        c.block_directory = Mock()
        c.sites_directory = Mock()
        c.json_directory.exists.return_value = True
        c.block_directory.exists.return_value = False
        c.sites_directory.exists.return_value = False

        with self.assertRaises(ValueError):
            c.initialize_skeleton()

        mock_load.assert_called_once()


class ControllerBuildTest(TestCase):
    def setUp(self):
        self.c = Controller()
        self.c._sites = [{"site_name": "this_site", "lang": "en"}]
        self.c.entrypoint = "aa_test"
        self.c.json_directory = "jj"
        self.c.block_directory = "bb"
        self.c.sites_directory = MagicMock()

    def test_site_not_supported(self):
        with self.assertRaises(ValueError):
            self.c.build("another_site", "en")

    @patch(PATH + ".Jinja2Parser")
    @patch(PATH + ".Site")
    @patch(PATH + ".Collector")
    def test_build(self, mock_c, mock_s, mock_jp):
        mock_c.collect_assets.return_value = {"block_js": "JS Code", "block_css": "CSS"}
        site = mock_s.return_value
        site.blocks = ["aa_test"]
        parser = mock_jp.return_value
        parser.parse_block.side_effect = lambda block, site_name, inline_blocks: {block: "Parsed j2 content."}

        self.c.build("this_site", "en")

        mock_c.collect_blocks.assert_called_once_with(self.c.json_directory)
        mock_s.assert_called_once_with("this_site", "en", root_name="aa_test")
        mock_s.return_value.setup_blocks.assert_called_once_with(mock_c.collect_blocks.return_value)
        mock_c.collect_assets.assert_called_once_with(block_dir=self.c.block_directory, blocks=list(site.blocks))
        mock_jp.assert_called_once_with(block_dir=self.c.block_directory)
        self.c.sites_directory.__truediv__.return_value.write_text.assert_called_once_with("Parsed j2 content.")

    @patch(PATH + ".Controller.build")
    def test_regenerate(self, mock_build):

        self.c.regenerate()

        mock_build.assert_called_once_with(site_name="this_site", lang="en")
