import json
import argparse
import os
from DSLinstanceToDSL.generator import SchemaGenerator


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="Name of DSL instance file (without .json)")
    parser.add_argument("--output", help="Optional output file name")

    args = parser.parse_args()

    # ------------------------------
    # Build correct input path
    # ------------------------------
    base_dir = os.path.dirname(os.path.abspath(__file__))

    input_path = os.path.join(
        base_dir,
        "data",
        "generated_dsls",
        f"{args.name}.json"
    )

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Could not find DSL instance at: {input_path}")

    # ------------------------------
    # Load DSL instance
    # ------------------------------
    with open(input_path, "r") as f:
        dsl_instance = json.load(f)

    dsl_instance_str = json.dumps(dsl_instance, indent=2)

    generator = SchemaGenerator()

    print(f"Loaded DSL instance from: {input_path}")
    print("Generating generalized DSL...\n")

    schema = generator.generate_schema(dsl_instance_str)

    # ------------------------------
    # Save output
    # ------------------------------
    output_filename = args.output if args.output else f"{args.name}_generalized.json"

    output_path = os.path.join(base_dir, "data", "generalized_dsl", output_filename)


    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"\nGeneralized DSL saved to: {output_path}")


if __name__ == "__main__":
    main()
