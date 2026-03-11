# generate_schema.py

import json
import argparse
import os
import glob

from DSLinstanceToDSL.generator import SchemaGenerator


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCES_DIR = os.path.join(BASE_DIR, "data", "generated_dsls")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "generalized_dsl")


def load_instance(name: str) -> dict:
    path = os.path.join(INSTANCES_DIR, f"{name}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Could not find DSL instance at: {path}")
    with open(path, "r") as f:
        return json.load(f)


def resolve_instances(names: list[str], use_all: bool) -> dict[str, dict]:
    """
    Return a dict of {name: dsl_instance}.
    If --all is set, load every .json in the instances directory.
    Otherwise load the explicitly named instances.
    """
    if use_all:
        paths = sorted(glob.glob(os.path.join(INSTANCES_DIR, "*.json")))
        if not paths:
            raise FileNotFoundError(f"No DSL instances found in {INSTANCES_DIR}")
        return {
            os.path.splitext(os.path.basename(p))[0]: json.load(open(p))
            for p in paths
        }

    if not names:
        raise ValueError("Provide at least one --name, or use --all.")

    return {name: load_instance(name) for name in names}


def main():
    parser = argparse.ArgumentParser(
        description="Generate a generalized DSL from one or more DSL instances.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
USAGE:

  # Single instance
  python generate_schema.py --name crash1_L0

  # Multiple specific instances
  python generate_schema.py --name crash1_L0 crash2_L1 crash3_L0

  # All instances in data/generated_dsls/
  python generate_schema.py --all

  # Custom output filename
  python generate_schema.py --all --output my_generalized.json
        """,
    )
    parser.add_argument(
        "--name",
        nargs="+",
        metavar="NAME",
        help="Name(s) of DSL instance file(s) (without .json). Ignored if --all is set.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Use all DSL instances found in data/generated_dsls/.",
    )
    parser.add_argument("--output", help="Output filename (saved to data/generalized_dsl/)")

    args = parser.parse_args()

    instances = resolve_instances(args.name or [], args.all)

    print(f"Loaded {len(instances)} instance(s): {', '.join(instances.keys())}")
    print("Generating generalized DSL...\n")

    generator = SchemaGenerator()
    schema = generator.generate_schema(instances)

    # ── Save output ───────────────────────────────────────────────────────────
    if args.output:
        output_filename = args.output
    elif len(instances) == 1:
        (name,) = instances.keys()
        output_filename = f"{name}_generalized.json"
    else:
        output_filename = "generalized.json"

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"Generalized DSL saved to: {output_path}")


if __name__ == "__main__":
    main()