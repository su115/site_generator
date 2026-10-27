import json
from typing import Any
from typing import List, Union
from pathlib import Path
from jsonschema import Draft202012Validator


class DFS:
    def __init__(self, target_path: List[str], debug: bool = False) -> None:
        self.found: bool = False
        self.value: Any
        self.line_number = 0
        self.target_path = target_path
        if not debug:
            self._check_value()

    def _check_value(self) -> None:
        if not self.target_path:
            raise ValueError("Target path cant be empty!")

    def _walk(self, data: Any, current_path: List[Union[str, int]]) -> int:
        if self.found:
            return self.line_number

        if current_path == self.target_path:
            self.found = True
            self.value = data

        if isinstance(data, dict):
            self.line_number += 1  # {
            for key, value in data.items():
                self._walk(value, current_path + [key])
                if self.found:
                    return self.line_number
        if isinstance(data, list):
            self.line_number += 1  # [
            for i, value in enumerate(data):
                self._walk(value, current_path + [i])
                if self.found:
                    return self.line_number
        self.line_number += 1  # ] or }
        return self.line_number

    def path_to_number(self, data: Any) -> int:
        line = self._walk(data, [])
        if self.found is False:
            raise KeyError(f"Path {self.target_path!r} not found")
        return line


class SchemaError(Exception):
    def __init__(self, message: str, validator: str, validator_value: str, instance: Any, path: List[str], data: Any) -> None:
        super().__init__(message)
        self._message = message
        self._validator = validator
        self._validator_value = validator_value
        self._instance = instance
        self._path = path

        self.data = data
        self._handlers = {
            "additionalProperties": self._handle_additional_properties,
        }

    @property
    def error_line(self) -> int:
        dfs = DFS(target_path=self.path)
        return dfs.path_to_number(self.data)

    @property
    def path(self) -> List[str]:
        return self._path.copy()

    @property
    def message(self) -> str:
        handler_method = self._handlers.get(self._validator, self._handle_unknown)
        return str(handler_method())

    def _handle_unknown(self) -> str:
        return self._message

    def _handle_additional_properties(self) -> str:
        if "Additional properties are not allowed" in self._message:
            key = self._message.split("('")[1].split("'")[0]
            self._path.append(key)
        return self._message

    def print_context(
        self,
        before: int = 5,
        after: int = 5,
    ) -> str:
        error_msg = ""
        lines = json.dumps(self.data, indent=4, ensure_ascii=False).splitlines()

        self._handle_additional_properties()
        error_line = self.error_line

        start = max(1, error_line - before)
        end = min(len(lines), error_line + after + 1)
        for i in range(start, end):
            marker = ">" if i == error_line else " "
            lineno = i  # human-readable
            content = lines[i - 1].rstrip()
            error_msg += f"{marker} {lineno:4d} | {content}\n"
        return error_msg


class SchemaValidator:
    def __init__(self, error_scope: int = 0) -> None:
        self.error_scope = error_scope

    def verify_json(self, main_schema: Any, data: Any) -> None:
        validator = Draft202012Validator(main_schema)
        for err in validator.iter_errors(data):
            print(err)
            error = SchemaError(
                data=data,
                path=list(err.absolute_path),
                message=err.message,
                validator=err.validator,
                validator_value=err.validator_value,
                instance=err.instance,
            )
            if self.error_scope != 0:
                print(error.print_context(self.error_scope, self.error_scope))
            raise error

    def verify_json_by_path(self, main_schema: Path, data: Any) -> None:
        raw_main_schema = main_schema.read_text()
        main_schema_dict = json.loads(raw_main_schema)
        self.verify_json(main_schema_dict, data)
