from unittest import TestCase
from sitegen.core.site import Content, Block


PATH = "sitegen.core.site"


class ContentTest(TestCase):
    def test_nested_init(self):
        dictionary = {"id": 1, "nested_dict": {"id": 2}, "nested_list": [{"id": 3}, 4, "other type", True]}
        obj = Content()

        obj.setup_fields(**dictionary)

        self.assertIsInstance(obj, Content)
        self.assertIsInstance(obj.nested_dict, Content)
        self.assertIsInstance(obj.nested_list[0], Content)
        self.assertIsInstance(obj.nested_list[1], int)

    def test_str(self):
        expected = """{
    "id": 1,
    "nested_dict": {
        "id": 2
    },
    "nested_list": [
        {
            "id": 3
        },
        4,
        "other type",
        true
    ]
}"""
        dictionary = {"id": 1, "nested_dict": {"id": 2}, "nested_list": [{"id": 3}, 4, "other type", True]}
        obj = Content()
        obj.setup_fields(**dictionary)

        result = str(obj)

        self.assertEqual(expected, result)

    def test_immutability(self):
        dictionary = {"id": 1, "nested_dict": {"id": 2}, "nested_list": [{"id": 3}, 4, "other type", True]}
        obj = Content()
        obj.setup_fields(**dictionary)

        with self.assertRaises(AttributeError):
            obj.id = 99

    def test_dict_immutability(self):
        dictionary = {"id": 1, "nested_dict": {"id": 2}, "nested_list": [{"id": 3}, 4, "other type", True]}
        obj = Content()
        obj.setup_fields(**dictionary)

        new_dict = obj.get_content_dict()
        new_dict["id"] = 99

        self.assertEqual(1, obj.id)
        self.assertIsNot(obj._kwargs, new_dict)

    def test_has_attr(self):
        dictionary = {"id": 1, "nested_dict": {"id": 2}, "nested_list": [{"id": 3}, 4, "other type", True]}
        obj = Content()
        obj.setup_fields(**dictionary)

        self.assertTrue(obj.has_attr("id"))
        self.assertTrue(obj.has_attr("nested_list"))
        self.assertTrue(obj.has_attr("nested_dict"))
        self.assertFalse(obj.has_attr("other_key"))

    def test_items(self):
        dictionary = {"id": 1, "nested_dict": {"id": 2}, "nested_list": [{"id": 3}, 4, "other type", True]}
        obj = Content()
        obj.setup_fields(**dictionary)
        expected = dictionary.copy()
        expected["nested_dict"] = obj.nested_dict
        expected["nested_list"] = [obj.nested_list[0], 4, "other type", True]

        result = {k: v for k, v in obj.items()}

        self.assertEqual(expected, result)


class BlockTest(TestCase):
    def test_has(self):
        dictionary = {
            "block_name": "aa",
            "content_type": "bb",
            "content_lang": "cc",
            "content": {"id": 1},
            "inline_blocks": "dd",
            "splited": True,
        }
        obj = Block()

        obj.setup_fields(**dictionary)

    def test_has_extra(self):
        dictionary = {
            "block_name": "aa",
            "content_type": "bb",
            "content_lang": "cc",
            "content": {"id": 1},
            "inline_blocks": "dd",
            "splited": True,
            "extra": "xx",
        }
        obj = Block()

        obj.setup_fields(**dictionary)

    def test_missed_required(self):
        dictionary = {
            "content_type": "bb",
            "content_lang": "cc",
            "content": {"id": 1},
            "inline_blocks": "dd",
            "splited": True,
        }
        obj = Block()

        with self.assertRaises(KeyError):
            obj.setup_fields(**dictionary)
