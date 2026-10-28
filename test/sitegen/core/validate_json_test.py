from unittest import TestCase

from parameterized import parameterized
from sitegen.core.validate_json import DFS

PATH = "sitegen.core.validate_json"


DATA1 = {"id": 1, "name": "Test", "active": True, "tags": ["demo", "example"]}
DATA2 = [0, DATA1, 2, 3]
DATA3 = [DATA1, 1, 2, DATA1]


class DFSTest(TestCase):
    def test_empty(self):
        tdata = []

        with self.assertRaises(ValueError):
            _ = DFS(tdata)

    @parameterized.expand(
        (
            (DATA1, ["tags", 1], 7),
            (DATA2, [1, "tags", 1], 9),
            (DATA3, [3, "id"], 14),
        )
    )
    def test_good_path(self, data, tpath, number):
        dfs = DFS(tpath)

        result_number = dfs.path_to_number(data)

        self.assertEqual(number, result_number)

    @parameterized.expand(
        (
            (DATA1, ["tags", 2]),
            (DATA1, [1]),
            (DATA1, ["id_not_exists"]),
            (DATA2, [1, "tags", 2]),
            (DATA3, [3, "id_not"]),
            (DATA3, [4, "id"]),
        )
    )
    def test_bad_path(self, data, tpath):
        dfs = DFS(tpath)

        with self.assertRaises(KeyError):
            _ = dfs.path_to_number(data)

    def test_cached_value(self):
        data, tpath, number = (DATA1, ["tags", 1], 7)
        dfs = DFS(tpath)

        _ = dfs.path_to_number(data)
        result_number = dfs.path_to_number(data)

        self.assertEqual(number, result_number)
