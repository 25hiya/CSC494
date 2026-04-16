# validate.py
from utils.schema_validator import SchemaValidator
from utils.files_io import load_json

validator = SchemaValidator.from_file("data/derived_schemas/schema_crash5_L6.json")

levels = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
for lv in levels:
    dsl = load_json(f"data/generated_dsls/crash5_{lv}.json")
    validator.validate_and_print(dsl, name=f"crash5_{lv}")
    print()