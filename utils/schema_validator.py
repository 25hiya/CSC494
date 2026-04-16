# evaluator/schema_validator.py
"""
Lightweight JSON Schema validator (draft-07 subset).
No external dependencies — works with the stdlib alone.

Supported keywords:
  type, required, properties, additionalProperties,
  items, minItems, enum, minimum, maximum,
  anyOf, $ref (within same schema file)

Usage:
    validator = SchemaValidator.from_file("data/dsl_schema.json")
    result = validator.validate(dsl_instance)

    result["valid"]          -> True / False
    result["error_count"]    -> int
    result["schema_score"]   -> 0.0-1.0
    result["errors"]         -> list of {path, message, keyword} dicts
"""

import json
from typing import Any


class SchemaValidator:

    def __init__(self, schema: dict):
        self.schema = schema
        self._defs = {
            **schema.get("$defs", {}),
            **schema.get("definitions", {}),
        }

    @classmethod
    def from_file(cls, path: str) -> "SchemaValidator":
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        return cls(schema)

    def validate(self, instance: Any) -> dict:
        errors: list[dict] = []
        self._validate_node(instance, self.schema, path="", errors=errors)

        top_required = self.schema.get("required", [])
        failed_top = {e["path"].split(".")[0].split("[")[0] for e in errors}
        schema_score = (
            round(1 - len(failed_top & set(top_required)) / len(top_required), 3)
            if top_required else (1.0 if not errors else 0.0)
        )

        return {
            "valid":        len(errors) == 0,
            "error_count":  len(errors),
            "schema_score": max(0.0, schema_score),
            "errors":       errors,
        }

    def validate_and_print(self, instance: Any, name: str = "") -> dict:
        result = self.validate(instance)
        label = f"[{name}] " if name else ""
        status = "VALID" if result["valid"] else f"{result['error_count']} error(s)"
        print(f"{label}Schema: {status}  (score={result['schema_score']:.2f})")
        for err in result["errors"]:
            path = err["path"] or "<root>"
            print(f"  [{err['keyword']}]  {path}  ->  {err['message']}")
        return result

    def _validate_node(self, instance, schema, path, errors):
        if "$ref" in schema:
            schema = self._resolve_ref(schema["$ref"])

        if "anyOf" in schema:
            self._check_any_of(instance, schema["anyOf"], path, errors)
            return

        if "type" in schema:
            if not self._check_type(instance, schema["type"], path, errors):
                return

        if "enum" in schema:
            self._check_enum(instance, schema["enum"], path, errors)

        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if "minimum" in schema and instance < schema["minimum"]:
                errors.append(_err(path, "minimum",
                    f"value {instance} is less than minimum {schema['minimum']}"))
            if "maximum" in schema and instance > schema["maximum"]:
                errors.append(_err(path, "maximum",
                    f"value {instance} exceeds maximum {schema['maximum']}"))

        if isinstance(instance, dict):
            self._check_required(instance, schema, path, errors)
            self._check_properties(instance, schema, path, errors)
            self._check_additional_properties(instance, schema, path, errors)

        if isinstance(instance, list):
            self._check_min_items(instance, schema, path, errors)
            self._check_items(instance, schema, path, errors)

    def _check_type(self, instance, type_spec, path, errors) -> bool:
        allowed = type_spec if isinstance(type_spec, list) else [type_spec]
        if _matches_types(instance, allowed):
            return True
        actual = "null" if instance is None else type(instance).__name__
        errors.append(_err(path, "type", f"expected {type_spec}, got {actual}"))
        return False

    def _check_enum(self, instance, allowed, path, errors):
        if instance not in allowed:
            errors.append(_err(path, "enum", f"'{instance}' is not one of {allowed}"))

    def _check_required(self, instance, schema, path, errors):
        for key in schema.get("required", []):
            if key not in instance:
                child = f"{path}.{key}" if path else key
                errors.append(_err(child, "required", f"'{key}' is a required property"))

    def _check_properties(self, instance, schema, path, errors):
        for key, sub_schema in schema.get("properties", {}).items():
            if key in instance:
                child_path = f"{path}.{key}" if path else key
                self._validate_node(instance[key], sub_schema, child_path, errors)

    def _check_additional_properties(self, instance, schema, path, errors):
        ap = schema.get("additionalProperties")
        known = set(schema.get("properties", {}).keys())
        if ap is False:
            for key in instance:
                if key not in known:
                    child = f"{path}.{key}" if path else key
                    errors.append(_err(child, "additionalProperties",
                        f"Additional property '{key}' is not allowed"))
        elif isinstance(ap, dict):
            for key, value in instance.items():
                if key not in known:
                    child = f"{path}.{key}" if path else key
                    self._validate_node(value, ap, child, errors)

    def _check_min_items(self, instance, schema, path, errors):
        min_items = schema.get("minItems")
        if min_items is not None and len(instance) < min_items:
            errors.append(_err(path, "minItems",
                f"array has {len(instance)} items; minimum is {min_items}"))

    def _check_items(self, instance, schema, path, errors):
        items_schema = schema.get("items")
        if items_schema is None:
            return
        for i, item in enumerate(instance):
            self._validate_node(item, items_schema, f"{path}[{i}]", errors)

    def _check_any_of(self, instance, sub_schemas, path, errors):
        for sub in sub_schemas:
            trial: list = []
            self._validate_node(instance, sub, path, trial)
            if not trial:
                return
        errors.append(_err(path, "anyOf", "value does not match any allowed schema"))

    def _resolve_ref(self, ref: str) -> dict:
        for prefix in ("#/$defs/", "#/definitions/"):
            if ref.startswith(prefix):
                name = ref[len(prefix):]
                if name in self._defs:
                    return self._defs[name]
        raise ValueError(f"Cannot resolve $ref: {ref}")


_JSON_TYPE_MAP = {
    "string":  str,
    "integer": int,
    "number":  (int, float),
    "boolean": bool,
    "array":   list,
    "object":  dict,
    "null":    type(None),
}


def _matches_types(instance, types: list) -> bool:
    for t in types:
        py_type = _JSON_TYPE_MAP.get(t)
        if py_type is None:
            continue
        if isinstance(instance, py_type):
            if t in ("integer", "number") and isinstance(instance, bool):
                continue
            return True
    return False


def _err(path: str, keyword: str, message: str) -> dict:
    return {"path": path, "keyword": keyword, "message": message}