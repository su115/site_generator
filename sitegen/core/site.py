from __future__ import annotations
from typing import List, Any, Dict, Tuple, Iterator
import copy
import json

Lang = str
ContentType = str


class Content:
    def __init__(self) -> None:
        self._kwargs: Dict[str, Any]

    def setup_fields(self, **kwargs: Dict[str, Any]) -> Content:
        self.__dict__["_kwargs"] = kwargs
        for key, value in self._kwargs.items():
            self.__dict__[key] = self._value_instantiation(value)

        self._setup_extra_fields()
        return self

    def _setup_extra_fields(self) -> None:
        pass

    def _value_instantiation(self, value: Any) -> Any:
        if isinstance(value, list):
            value_list = []
            for item in value:
                value_list.append(self._value_instantiation(item))
            return value_list
        if isinstance(value, dict):
            content = Content()
            content.setup_fields(**value)
            return content
        return value

    def __str__(self) -> str:
        new_dict = self._kwargs.copy()
        return json.dumps(new_dict, indent=4, ensure_ascii=False)

    def __setattr__(self, attr: str, value: Any) -> None:
        raise AttributeError("Cannot modify attributes of a frozen object")

    def has_attr(self, attr: str) -> bool:
        return hasattr(self, attr)

    def items(self) -> Iterator[Tuple[str, Any]]:
        for key in self._kwargs.keys():
            yield key, self.__dict__[key]

    def get_content_dict(self) -> Dict[str, Any]:
        return copy.deepcopy(self._kwargs)


class Block(Content):
    def __init__(self) -> None:
        self.inline_blocks: List[str]
        self.splited: bool
        self.block_name: str
        self.content_type: ContentType
        self.content_lang: Lang
        self.content: Content

        self.__dict__["inline_blocks"] = []
        self.__dict__["splited"] = False

    def _setup_extra_fields(self) -> None:
        reserved = ["inline_blocks", "splited", "block_name", "content_type", "content_lang", "content"]
        for key in reserved:
            if key not in self.__dict__:
                msg = f"Dictionary is not following format! Key {key!r} not found!"
                raise KeyError(msg)


class Site:
    def __init__(self, site_name: str, lang: Lang, root_name: str) -> None:
        self._blocks: List[Block] = []
        self.site_name = site_name
        self.lang = lang
        self._root_name = root_name

    @property
    def root_name(self) -> str:
        return self._root_name

    @property
    def blocks(self) -> Iterator[Block]:
        for block in self._blocks:
            yield block

    def setup_blocks(self, all_blocks: List[Block]) -> None:
        langs = ["common", self.lang]
        same_lang_blocks = [b for b in all_blocks if b.content_lang in langs]

        content_type = ["common", "shared", self.site_name]
        same_site_blocks = [b for b in same_lang_blocks if b.content_type in content_type]

        self._check_block_names(same_site_blocks)

        self._blocks = self._sort_order_by_dependecies(self.root_name, same_site_blocks)

    def _check_block_names(self, blocks: List[Block]) -> None:
        names = {}
        for block in blocks:
            if block.block_name in names:
                msg = f"Found duplication {block.block_name}"
                raise ValueError(msg)

            names[block.block_name] = block

    def _sort_order_by_dependecies(self, root_name: str, blocks: List[Block]) -> List[Block]:
        graph = {b.block_name: b.inline_blocks for b in blocks}
        visited = set()
        temp = set()
        result = []

        def dfs(node: str) -> None:
            if node in temp:
                raise ValueError(f"Cycle detected at {node}")
            if node in visited:
                return
            temp.add(node)
            for dep in graph.get(node, []):
                if dep not in graph:
                    raise ValueError(f"Dependecy {dep} is not part of dependecy tree!")
                dfs(node=dep)
            temp.remove(node)
            visited.add(node)
            result.append(node)

        dfs(root_name)
        name_to_block = {b.block_name: b for b in blocks}
        return [name_to_block[name] for name in result]
