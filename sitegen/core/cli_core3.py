from __future__ import annotations
from pathlib import Path
from typing import List, Dict
import copy
import json
import yaml
import shutil
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template
from sitegen.core.validate_json import SchemaValidator
from sitegen.core.site import Site, Block

Lang = str
ContentType = str


class Collector:
    @classmethod
    def collect_blocks(cls, json_dir: Path) -> List[Block]:
        block_list = []
        for json_file in Path(json_dir).glob("*.json"):
            raw_json_data = json_file.read_text(encoding="utf-8")
            json_data = json.loads(raw_json_data)
            if not isinstance(json_data, list):
                msg = f"Expected Block list, got: {type(json_data)}, {json_data}"
                raise ValueError(msg)

            for block_dict in json_data:
                if not isinstance(block_dict, dict):
                    msg = f"Expected Block dictionary, got: {type(block_dict)}, {block_dict}"
                    raise ValueError(msg)

                block = Block()
                block.setup_fields(**block_dict)
                block_list.append(block)
        return block_list


class Jinja2Parser:
    def __init__(self, site: Site, block_dir: Path) -> None:
        self.site = site
        self.block_dir = block_dir
        self.blocks_dict: Dict[str, str] = {}
        self.text_css: str = ""
        self.text_js: str = ""

    def _validate_block(self, block: Block) -> None:
        schema_path = self.block_dir / block.block_name / "content.schema"
        sc = SchemaValidator(3)
        sc.verify_json_by_path(schema_path, block.content.get_content_dict())
        print(f"Validate {schema_path}.")

    def _load_assets(self, block: Block) -> None:
        css_file = self.block_dir / block.block_name / "base.css"
        if css_file.exists():
            self.text_css += "\n" + css_file.read_text(encoding="utf-8")
        js_file = self.block_dir / block.block_name / "base.js"
        if js_file.exists():
            self.text_js += "\n" + js_file.read_text(encoding="utf-8")

    def _get_template(self, block: Block) -> Template:
        env = Environment(
            loader=FileSystemLoader(str(self.block_dir)),
            undefined=StrictUndefined,
            autoescape=False,
        )
        env.globals["raise"] = RuntimeError
        template_path = Path(block.block_name) / "base.j2"
        return env.get_template(str(template_path))

    def parse_block(self, block: Block) -> None:
        self._validate_block(block)

        print(f"Parse block: {block.block_name!r} ...", end="")
        template = self._get_template(block)
        self._load_assets(block)

        template_dictionary = {
            "content": block.content,
            "site_name": self.site.site_name,
            "inline_blocks": self.blocks_dict.copy(),
            "text_css": self.text_css,
            "text_js": self.text_js,
        }
        result = template.render(**template_dictionary)

        self.blocks_dict.update(self.split_content(block.block_name, result))
        print(" [OK]")

    def split_content(self, block_name: str, data: str) -> Dict[str, str]:
        splited_data = data.split("<!-- SPLIT -->")
        if len(splited_data) == 1:
            return {block_name: data}
        result = {}
        for number, part in enumerate(splited_data):
            result[f"{block_name}_part{number + 1}"] = part
        return result

    def parse_site(self) -> str:
        for block in self.site.blocks:
            self.parse_block(block)
        return self.blocks_dict[self.site.root_name]


BASE_PATH = Path(__file__).resolve().parent.parent
CONFIG_SCHEMA_PATH = BASE_PATH / "config_schema.json"


class Controller:
    def __init__(self, config_file: str = "sitegen.yaml") -> None:
        self.config_file = config_file
        self._sites: List[Dict[str, str]] = []
        self.entrypoint: str

        self.json_directory: Path
        self.block_directory: Path
        self.sites_directory: Path

    @property
    def sites(self) -> List[Dict[str, str]]:
        return copy.deepcopy(self._sites)

    def load_config(self) -> None:
        config_path = Path(self.config_file)
        if not config_path.exists():
            raise ValueError(f"Config {self.config_file} not found!")

        raw_config_yaml = config_path.read_text(encoding="utf-8")
        config_yaml = yaml.safe_load(raw_config_yaml)

        sc = SchemaValidator(5)
        sc.verify_json_by_path(CONFIG_SCHEMA_PATH, config_yaml)

        self.entrypoint = config_yaml["block_entrypoint"]

        self.json_directory = Path(config_yaml["json_directory"])
        self.block_directory = Path(config_yaml["block_directory"])
        self.sites_directory = Path(config_yaml["sites_directory"])

        self._sites = [{"site_name": s["name"], "lang": s["lang"]} for s in config_yaml["sites"]]

    def initialize_skeleton(self) -> None:
        if self.json_directory.exists() or self.block_directory.exists() or self.sites_directory.exists():
            msg = f"""Please cleanup environment!
{str(self.json_directory)!r} or {str(self.block_directory)!r} or {str(self.sites_directory)!r} exists!
"""
            raise ValueError(msg)
        self.json_directory.mkdir(exist_ok=True, parents=True)
        self.block_directory.mkdir(exist_ok=True, parents=True)
        self.sites_directory.mkdir(exist_ok=True, parents=True)

        shutil.copytree(BASE_PATH / "skel/block", self.block_directory, dirs_exist_ok=True)
        shutil.copytree(BASE_PATH / "skel/json_backbone", self.json_directory, dirs_exist_ok=True)


def main(
    site_name: str,
    lang: str,
) -> None:
    c = Controller()
    c.load_config()

    if {"site_name": site_name, "lang": lang} not in c.sites:
        msg = f"Site {site_name!r} with lang {lang!r} is not supported!"
        raise ValueError(msg)

    blocks = Collector.collect_blocks(c.json_directory)

    site = Site(site_name, lang, root_name=c.entrypoint)
    site.setup_blocks(blocks)

    parser = Jinja2Parser(site=site, block_dir=c.block_directory)
    file_content = parser.parse_site()

    site_file = c.sites_directory / f"{site_name}_{lang}.html"
    site_file.write_text(file_content)


if __name__ == "__main__":  # pragma: no cover
    import sys

    print(sys.argv)
    if len(sys.argv) == 3:
        name = sys.argv[1]
        lang = sys.argv[2]
        main(name, lang)
    else:
        print("Example: python3 sitegen/core/cli_core3.py example en")
