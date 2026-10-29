from unittest import TestCase
from unittest.mock import Mock, patch

from sitegen.cli import build, complete_lang, complete_site, get_sites, init, regenerate

PATH = "sitegen.cli"


class CliTest(TestCase):
    @patch(PATH + ".Controller")
    def test_build(self, mock_build):
        build("s1", "en")

        mock_build.assert_called_once()
        mock_build.return_value.load_config.assert_called_once()
        mock_build.return_value.load_config.return_value.build.assert_called_once_with(site_name="s1", lang="en")

    @patch(PATH + ".Controller")
    def test_regenerate(self, mock_reg):
        regenerate()

        mock_reg.assert_called_once()
        mock_reg.return_value.load_config.assert_called_once()
        mock_reg.return_value.load_config.return_value.regenerate.assert_called_once_with()

    @patch(PATH + ".Controller")
    def test_init(self, mock_init):
        init()

        mock_init.assert_called_once()
        mock_init.return_value.initialize_skeleton.assert_called_once()


SITES = [
    {"site_name": "site_1", "lang": "ua"},
    {"site_name": "site_2", "lang": "pl"},
    {"site_name": "another_1", "lang": "en"},
    {"site_name": "this_1", "lang": "ru"},
]


class ComplectionTest(TestCase):
    @patch(PATH + ".Controller")
    def test_get_sites(self, mock_cnt):
        result = get_sites()

        mock_cnt.assert_called_once()
        mock_cnt.return_value.load_config.assert_called_once()
        self.assertEqual(mock_cnt.return_value.load_config.return_value.sites, result)

    @patch(PATH + ".get_sites", return_value=SITES)
    def test_complete_site_found(self, mock_gs):
        result = complete_site("s")

        self.assertEqual(["site_1", "site_2"], result)

    @patch(PATH + ".get_sites", return_value=SITES)
    def test_complete_site_not_found(self, mock_gs):
        result = complete_site("z")

        self.assertEqual([], result)

    @patch(PATH + ".get_sites", return_value=SITES)
    def test_complete_lang_found(self, mock_gs):
        ctx = Mock(params={"site": "site_2"})
        result = complete_lang(ctx, "p")

        self.assertEqual(["pl"], result)

    @patch(PATH + ".get_sites", return_value=SITES)
    def test_complete_lang_not_found(self, mock_gs):
        ctx = Mock(params={"site": "site_3"})
        result = complete_lang(ctx, "ua")

        self.assertEqual([], result)
