# build_schema.py
"""
Algorithmically derives a JSON Schema from one or more DSL instances.

For each key encountered it infers the type. When the same key appears
across multiple instances with different types or structures, those are
merged/unioned so the schema covers all of them.

USAGE:

  # Build from all levels of crash2
  python build_schema.py --prefix crash2

  # Build from specific levels only
  python build_schema.py --names crash2_L4 crash2_L5 crash2_L6

  # Build from just L6 (manual gold standard equivalent)
  python build_schema.py --names crash2_L6

  # Custom output name
  python build_schema.py --prefix crash2 --output crash2_schema.json

Output is saved to data/derived_schemas/
"""

import argparse
import glob
import json
import os

from utils.files_io import load_json, save_json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCES_DIR = os.path.join(BASE_DIR, "data", "generated_dsls")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "derived_schemas")

# Keys to skip entirely (timestamps, internal bookkeeping)
SKIP_KEYS = {"last_updated", "metadata"}


# ── Type inference ─────────────────────────────────────────────────────────────

def infer_type(value) -> str:
    """Map a Python value to its JSON Schema type string."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "string"


def merge_types(existing: list[str], new_type: str) -> list[str]:
    """
    Keep a running union of all types seen for a field.
    Returns a sorted list so output is deterministic.
    """
    merged = set(existing) | {new_type}
    return sorted(merged)


# ── Core schema builder ────────────────────────────────────────────────────────

def build_schema_from_value(value, key_name: str = "") -> dict:
    """
    Recursively build a schema node from a single value.
    """
    t = infer_type(value)

    if t == "object":
        return build_schema_from_object(value)

    if t == "array":
        return build_schema_from_array(value, key_name)

    # Leaf — just a type node
    return {"type": t}


def build_schema_from_object(obj: dict) -> dict:
    """Build a schema node for a dict, recursing into each property."""
    if not obj:
        return {"type": "object"}

    properties = {}
    for key, value in obj.items():
        if key in SKIP_KEYS:
            continue
        properties[key] = build_schema_from_value(value, key_name=key)

    return {
        "type": "object",
        "properties": properties,
        "required": sorted(properties.keys()),
    }


def build_schema_from_array(lst: list, key_name: str = "") -> dict:
    """
    Build a schema node for a list.
    If the list contains objects, merge all items into one representative
    items schema so the schema covers every key seen across all elements.
    """
    if not lst:
        return {"type": "array"}

    # Merge all items into one representative schema
    merged_items: dict = {}
    for item in lst:
        item_schema = build_schema_from_value(item, key_name)
        merged_items = merge_object_schemas(merged_items, item_schema)

    return {
        "type": "array",
        "minItems": 1,
        "items": merged_items,
    }


# ── Schema merging ─────────────────────────────────────────────────────────────

def merge_object_schemas(schema_a: dict, schema_b: dict) -> dict:
    """
    Merge two schema nodes together.

    - Types are unioned (if a field is "string" in one instance and "integer"
      in another, the merged schema allows both).
    - Properties are unioned (every key seen across all instances is included).
    - required contains only keys present in BOTH schemas (intersection),
      since a key absent from one instance shouldn't be required globally.
    """
    if not schema_a:
        return schema_b
    if not schema_b:
        return schema_a

    # Merge top-level type
    types_a = schema_a.get("type", [])
    types_b = schema_b.get("type", [])
    if isinstance(types_a, str):
        types_a = [types_a]
    if isinstance(types_b, str):
        types_b = [types_b]
    merged_types = sorted(set(types_a) | set(types_b))
    merged_type = merged_types[0] if len(merged_types) == 1 else merged_types

    result: dict = {"type": merged_type}

    # Merge properties (union of all keys)
    props_a = schema_a.get("properties", {})
    props_b = schema_b.get("properties", {})

    if props_a or props_b:
        all_keys = set(props_a) | set(props_b)
        merged_props = {}
        for key in all_keys:
            if key in props_a and key in props_b:
                merged_props[key] = merge_object_schemas(props_a[key], props_b[key])
            elif key in props_a:
                merged_props[key] = props_a[key]
            else:
                merged_props[key] = props_b[key]
        result["properties"] = merged_props

        # required = only keys present in both (intersection = truly required)
        req_a = set(schema_a.get("required", list(props_a.keys())))
        req_b = set(schema_b.get("required", list(props_b.keys())))
        required = sorted(req_a & req_b)
        if required:
            result["required"] = required

    # Merge array items schemas
    items_a = schema_a.get("items")
    items_b = schema_b.get("items")
    if items_a or items_b:
        if items_a and items_b:
            result["items"] = merge_object_schemas(items_a, items_b)
        else:
            result["items"] = items_a or items_b
        result["minItems"] = min(
            schema_a.get("minItems", 1),
            schema_b.get("minItems", 1),
        )

    return result


# ── Top-level builder ──────────────────────────────────────────────────────────

def build_schema(instances: dict[str, dict]) -> dict:
    """
    Given a dict of {name: dsl_instance}, merge all instances into
    a single JSON Schema that covers every key and type seen.
    """
    print(f"\nBuilding schema from {len(instances)} instance(s):")
    merged: dict = {}

    for name, instance in instances.items():
        print(f"  Processing {name}...")

        # Strip metadata from the top level before processing
        clean = {k: v for k, v in instance.items() if k not in SKIP_KEYS}
        instance_schema = build_schema_from_object(clean)
        merged = merge_object_schemas(merged, instance_schema)

    # Add JSON Schema boilerplate
    merged["$schema"] = "http://json-schema.org/draft-07/schema#"
    merged["title"] = "CrashDSL (algorithmically derived)"
    merged["description"] = (
        f"Schema derived from: {', '.join(instances.keys())}"
    )

    return merged


# ── Loader helpers ─────────────────────────────────────────────────────────────

def load_by_prefix(prefix: str) -> dict[str, dict]:
    pattern = os.path.join(INSTANCES_DIR, f"{prefix}_L*.json")
    paths = sorted(glob.glob(pattern))
    if not paths:
        raise FileNotFoundError(
            f"No instances found for prefix '{prefix}' in {INSTANCES_DIR}"
        )
    return {
        os.path.splitext(os.path.basename(p))[0]: load_json(p)
        for p in paths
    }


def load_by_names(names: list[str]) -> dict[str, dict]:
    result = {}
    for name in names:
        path = os.path.join(INSTANCES_DIR, f"{name}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Instance not found: {path}")
        result[name] = load_json(path)
    return result


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Algorithmically derive a JSON Schema from DSL instances.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--prefix", type=str,
        help="Load all <prefix>_L*.json files from data/generated_dsls/",
    )
    group.add_argument(
        "--names", nargs="+", metavar="NAME",
        help="Explicit list of instance names (without .json)",
    )
    parser.add_argument(
        "--output", type=str,
        help="Output filename (saved to data/derived_schemas/)",
    )
    parser.add_argument(
        "--pretty", action="store_true", default=True,
        help="Pretty-print the output JSON (default: true)",
    )
    args = parser.parse_args()

    # Load
    if args.prefix:
        instances = load_by_prefix(args.prefix)
        default_output = f"{args.prefix}_derived_schema.json"
    else:
        instances = load_by_names(args.names)
        default_output = "derived_schema.json"

    # Build
    schema = build_schema(instances)

    # Save
    output_name = args.output or default_output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, output_name)
    save_json(schema, output_path)

    print(f"\nDerived schema saved to: {output_path}")
    _print_summary(schema)


def _print_summary(schema: dict):
    top_keys = list(schema.get("properties", {}).keys())
    required = schema.get("required", [])
    optional = [k for k in top_keys if k not in required]

    print(f"\nSchema summary:")
    print(f"  Top-level required : {required}")
    print(f"  Top-level optional : {optional}")

    for section, props in schema.get("properties", {}).items():
        sub_props = props.get("properties", {})
        if sub_props:
            print(f"  {section} keys      : {sorted(sub_props.keys())}")
        elif props.get("type") == "array":
            item_props = props.get("items", {}).get("properties", {})
            if item_props:
                print(f"  {section}[] keys    : {sorted(item_props.keys())}")


if __name__ == "__main__":
    main()