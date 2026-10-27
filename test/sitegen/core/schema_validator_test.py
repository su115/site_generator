from unittest import TestCase
from unittest.mock import Mock
from sitegen.core.validate_json import SchemaValidator, SchemaError

PATH = "sitegen.core.validate_json"


SCHEMA = Mock()
SCHEMA.read_text.return_value = """{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "User",
  "type": "object",
  "properties": {
    "id": {
      "type": "integer",
      "example": 123
    },
    "name": {
      "type": "string",
      "example": "John"
    },
    "active": {
      "type": "boolean",
      "example": true
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "example": ["demo", "test"]
    }
  },
  "required": ["id", "name", "active", "tags"],
  "additionalProperties": false
}"""


class SchemaValidatorTest(TestCase):
    def test_without_issue(self):
        data = {"id": 123, "name": "John", "active": True, "tags": ["demo", "test"]}
        validator = SchemaValidator()

        result = validator.verify_json_by_path(SCHEMA, data)

        self.assertIsNone(result)

    def test_with_issue(self):
        data = {
            "id": 123,
            "name": False,
            "active": True,
            "tags": ["demo", "test"],
        }
        validator = SchemaValidator(5)

        with self.assertRaises(SchemaError):
            validator.verify_json_by_path(SCHEMA, data)

    def test_with_issue_additional_properties(self):
        data = {"id": 123, "name": "Error", "active": True, "tags": ["demo", "test"], "not_expected": 13}
        validator = SchemaValidator(5)

        with self.assertRaises(SchemaError):
            validator.verify_json_by_path(SCHEMA, data)

    def test_exception_message_additional_properties(self):
        data = {"id": 123, "name": "Error", "active": True, "tags": ["demo", "test"], "not_expected": 13}
        msg = """Additional properties are not allowed (\'not_expected\' was unexpected)"""
        validator = SchemaValidator(5)

        try:
            validator.verify_json_by_path(SCHEMA, data)
        except SchemaError as e:
            self.assertEqual(msg, e.message)

    def test_exception_message(self):
        data = {
            "id": 123,
            "name": False,
            "active": True,
            "tags": ["demo", "test"],
        }
        msg = "False is not of type 'string'"
        validator = SchemaValidator(5)

        try:
            validator.verify_json_by_path(SCHEMA, data)
        except SchemaError as e:
            self.assertEqual(msg, e.message)
