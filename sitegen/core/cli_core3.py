from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template

from sitegen.core.site import Block, Site
from sitegen.core.validate_json import SchemaValidator

Lang = str
ContentType = str


class Collector:
    @classmethod
    def collect_blocks(cls, json_dir: Path) -> list[Block]:
        block_list = []
        for json_file in json_dir.glob("*.json"):
            raw_json_data = json_file.read_text(encoding="utf-8")
            json_data = json.loads(raw_json_data)
            if not isinstance(json_data, list):
                msg = f"Expected Block list, got: {type(json_data)}, {json_data}"
                raise TypeError(msg)

            for block_dict in json_data:
                if not isinstance(block_dict, dict):
                    msg = f"Expected Block dictionary, got: {type(block_dict)}, {block_dict}"
                    raise TypeError(msg)

                block = Block()
                block.setup_fields(**block_dict)
                block_list.append(block)
        return block_list

    @classmethod
    def _get_asset_content(cls, block_dir: Path, block_name: str, file: str) -> str:
        asset_file = block_dir / block_name / file
        if asset_file.exists():
            return "\n" + asset_file.read_text(encoding="utf-8")
        return ""

    @classmethod
    def collect_assets(cls, blocks: list[Block], block_dir: Path) -> dict[str, str]:
        text_css = ""
        text_js = ""
        for block in blocks:
            text_css = cls._get_asset_content(block_dir, block.block_name, "base.css")
            text_js = cls._get_asset_content(block_dir, block.block_name, "base.js")
        return {
            "block_css": text_css,
            "block_js": text_js,
        }


class Jinja2Parser:
    def __init__(self, block_dir: Path) -> None:
        self.block_dir = block_dir
        self.text_css: str = ""
        self.text_js: str = ""

    def _validate_block(self, block: Block) -> None:
        schema_path = self.block_dir / block.block_name / "content.schema"
        sc = SchemaValidator(3)
        sc.verify_json_by_path(schema_path, block.content.get_content_dict())
        print(f"Validate {schema_path}.")

    def _get_template(self, block: Block) -> Template:
        env = Environment(
            loader=FileSystemLoader(str(self.block_dir)),
            undefined=StrictUndefined,
            autoescape=False,
        )
        env.globals["raise"] = RuntimeError
        template_path = Path(block.block_name) / "base.j2"
        return env.get_template(str(template_path))

    def parse_block(self, block: Block, site_name: str, inline_blocks: dict[str, str]) -> dict[str, str]:
        self._validate_block(block)

        print(f"Parse block: {block.block_name!r} ...", end="")
        template = self._get_template(block)

        template_dictionary = {
            "content": block.content,
            "site_name": site_name,
            "inline_blocks": inline_blocks.copy(),
        }
        result = template.render(**template_dictionary)

        print(" [OK]")
        return self._split_content(block.block_name, result)

    def _split_content(self, block_name: str, data: str) -> dict[str, str]:
        splited_data = data.split("<!-- SPLIT -->")
        if len(splited_data) == 1:
            return {block_name: data}
        result = {}
        for number, part in enumerate(splited_data):
            result[f"{block_name}_part{number + 1}"] = part
        return result


BASE_PATH = Path(__file__).resolve().parent.parent
CONFIG_SCHEMA_PATH = BASE_PATH / "config_schema.json"


class Controller:
    def __init__(self, config_file: str = "sitegen.yaml") -> None:
        self.config_file = config_file
        self._sites: list[dict[str, str]] = []
        self.entrypoint: str

        self.json_directory: Path
        self.block_directory: Path
        self.sites_directory: Path

    @property
    def sites(self) -> list[dict[str, str]]:
        return copy.deepcopy(self._sites)

    def load_config(self) -> Controller:
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
        return self

    def initialize_skeleton(self) -> None:
        config_file = Path(self.config_file)
        if not config_file.is_file():
            print(f"Config file not found {str(config_file)!r}!")
            shutil.copy(BASE_PATH / "skel/sitegen.yaml", config_file)
            print("Config file was generated!")

        self.load_config()
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

    def build(self, site_name: str, lang: str) -> None:
        if {"site_name": site_name, "lang": lang} not in self.sites:
            msg = f"Site {site_name!r} with lang {lang!r} is not supported!"
            raise ValueError(msg)

        blocks = Collector.collect_blocks(self.json_directory)

        site = Site(site_name, lang, root_name=self.entrypoint)
        site.setup_blocks(blocks)

        # parse logic
        block_dict: dict[str, str] = Collector.collect_assets(block_dir=self.block_directory, blocks=list(site.blocks))
        parser = Jinja2Parser(block_dir=self.block_directory)
        for block in site.blocks:
            block_dict.update(parser.parse_block(block=block, site_name=site_name, inline_blocks=block_dict.copy()))
        file_content = block_dict[self.entrypoint]

        site_file = self.sites_directory / f"{site_name}_{lang}.html"
        site_file.write_text(file_content)

    def regenerate(self) -> None:
        print("Regenerating...")
        msg = ""
        for site in self.sites:
            site_name = site["site_name"]
            lang = site["lang"]
            self.build(site_name=site_name, lang=lang)
            msg += f"Site: {str(site_name).ljust(30)} {lang} regenerated.\n"
        print(msg)


if __name__ == "__main__":  # pragma: no cover
    import sys

    print(sys.argv)
    if len(sys.argv) == 3:
        sname = sys.argv[1]
        lang = sys.argv[2]

        c = Controller()
        c.load_config()
        c.build(sname, lang)
    else:
        print("Example: python3 sitegen/core/cli_core3.py example en")
