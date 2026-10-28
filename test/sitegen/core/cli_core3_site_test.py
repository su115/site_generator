from unittest import TestCase
from unittest.mock import patch

from sitegen.core.site import Block, Site

PATH = "sitegen.core.site"


def blocker(block_name, content_lang, content_type, inline_blocks, content=0):
    return Block().setup_fields(
        block_name=block_name,
        content_lang=content_lang,
        content_type=content_type,
        content=content,
        inline_blocks=inline_blocks,
    )


def sort_deps(rname, sblocks):
    return sblocks


class SiteContentLangTest(TestCase):
    @patch(PATH + ".Site._sort_order_by_dependecies", side_effect=sort_deps)
    def setUp(self, sort_dep):
        self.site = Site(site_name="test_site", lang="ua", root_name="aa")
        blocks = [
            blocker("aa", "common", "common", ["bb", "cc"]),
            blocker("bb", "ua", "common", []),
            blocker("cc", "ru", "common", []),
        ]
        self.site.setup_blocks(blocks)

        self.result = [b.block_name for b in self.site.blocks]

    def test_common_lang_blocks_allways_included(self):
        self.assertIn("aa", self.result)

    def test_site_lang_allways_included(self):
        self.assertIn("bb", self.result)

    def test_other_lang_allways_missed(self):
        self.assertNotIn("cc", self.result)


class SiteContentTypeTest(TestCase):
    @patch(PATH + ".Site._sort_order_by_dependecies", side_effect=sort_deps)
    def setUp(self, sort_dep):
        self.site = Site(site_name="test_site", lang="ua", root_name="aa")
        blocks = [
            blocker("aa", "common", "common", ["bb", "cc", "dd", "ee"]),
            blocker("bb", "common", "shared", []),
            blocker("cc", "common", "test_site", []),
            blocker("dd", "common", "another_site", []),
            blocker("ee", "common", "common", []),
        ]
        self.site.setup_blocks(blocks)
        self.result = [b.block_name for b in self.site.blocks]

    def test_common_type_is_available(self):
        self.assertIn("ee", self.result)
        self.assertIn("aa", self.result)

    def test_shared_type_is_available(self):
        self.assertIn("bb", self.result)

    def test_same_site_name_is_available(self):
        self.assertIn("cc", self.result)

    def test_another_site_name_is_not_availanle(self):
        self.assertNotIn("dd", self.result)


class SiteDFSTest(TestCase):
    def setUp(self):
        self.site = Site(site_name="test_site", lang="ua", root_name="aa")
        blocks = [
            blocker("aa", "common", "common", ["bb"]),
            blocker("bb", "common", "common", ["dd"]),
            blocker("cc", "common", "common", []),
            blocker("dd", "common", "common", []),
        ]
        self.site.setup_blocks(blocks)
        self.result = [b.block_name for b in self.site.blocks]

    def test_chain_blocks_included(self):
        self.assertIn("aa", self.result)
        self.assertIn("bb", self.result)
        self.assertIn("dd", self.result)

    def test_chain_block_order(self):
        self.assertEqual(["dd", "bb", "aa"], self.result)

    def test_missed_block(self):
        self.assertNotIn("cc", self.result)


class SiteEdgeTest(TestCase):
    def setUp(self):
        self.site = Site(site_name="test_site", lang="ua", root_name="aa")

    def test_wrong_root_name(self):
        blocks = [
            blocker("zz", "common", "common", []),
        ]
        with self.assertRaises(KeyError):
            self.site.setup_blocks(blocks)

    def test_empty_input_list(self):
        with self.assertRaises(KeyError):
            self.site.setup_blocks([])

    def test_cycle_deps(self):
        blocks = [
            blocker("aa", "common", "common", ["bb"]),
            blocker("bb", "common", "common", ["cc"]),
            blocker("cc", "common", "common", ["bb"]),
        ]
        with self.assertRaises(ValueError):
            self.site.setup_blocks(blocks)

    def test_torn_off_dep(self):
        blocks = [
            blocker("aa", "common", "common", ["bb"]),
            blocker("bb", "common", "common", ["cc"]),
            blocker("cc", "common", "common", ["zz"]),
        ]
        with self.assertRaises(ValueError):
            self.site.setup_blocks(blocks)

    def test_block_name_duplicates_is_not_allowed(self):
        blocks = [
            blocker("aa", "common", "common", ["bb", "cc"]),
            blocker("bb", "common", "common", []),
            blocker("bb", "common", "common", []),
            blocker("cc", "common", "common", []),
        ]
        with self.assertRaises(ValueError):
            self.site.setup_blocks(blocks)
