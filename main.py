# main.py

import argparse
import json

from llm.client import get_llm
from llm.prompts import get_initial_prompt, get_refine_prompt
from llm.parser import get_parser
from dsl.memory import load_previous_dsl, save_new_version
from utils.files_io import load_text
from config import CRASH_REPORT_PATH


def call_llm(chain, parser, inputs, max_retries=3):
    for attempt in range(max_retries):
        print(f"\nLLM attempt {attempt + 1}")

        result = chain.invoke(inputs)
        print("Raw output (first 500 chars):")
        print(result.content[:500])

        try:
            parsed = parser.parse(result.content)
            print("Parsing successful.")
            return parsed
        except Exception as e:
            print("Parsing failed:", e)
            print("Retrying...\n")

    raise RuntimeError("LLM failed to produce valid JSON after retries.")


def generate_dsl(name: str, crash_report: str):
    """Generate initial DSL with schema validation."""
    parser = get_parser(validate=True)  # ← Validate for initial generation
    llm = get_llm()
    prompt = get_initial_prompt(parser)
    chain = prompt | llm

    dsl_obj = call_llm(chain, parser, {"crash_report": crash_report})
    
    # Convert Pydantic model to dict
    if hasattr(dsl_obj, 'model_dump'):
        return dsl_obj.model_dump()
    else:
        return dsl_obj  # Already a dict


def refine_dsl(name: str, hints: str, crash_report: str ):
    """Refine DSL WITHOUT schema validation."""
    previous = load_previous_dsl(name)

    if previous is None:
        raise ValueError("No previous DSL found. Generate first.")

    print(f"📝 Applying hints: {hints}")
    print(f"⏳ This may take 1-3 minutes for complex refinements...")
    print(f"⚠️  Schema validation DISABLED - structure can evolve freely\n", flush=True)

    parser = get_parser(validate=False)  # ← NO validation for refinement!
    llm = get_llm()
    prompt = get_refine_prompt(parser)
    chain = prompt | llm

    dsl_dict = call_llm(
        chain,
        parser,
        {
            "crash_report": crash_report,
            "previous_dsl": json.dumps(previous, indent=2),
            "hints": hints,
        },
    )

    return dsl_dict  # Already a dict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["generate", "refine"], required=True)
    parser.add_argument("--name", type=str, required=True)
    parser.add_argument("--crash_file", type=str)
    parser.add_argument("--hints", type=str)

    args = parser.parse_args()

    if args.mode == "generate":
        if not args.crash_file:
            raise ValueError("Must provide --crash_file")

        crash_report = load_text(CRASH_REPORT_PATH + args.crash_file)
        dsl_dict = generate_dsl(args.name, crash_report)
        save_new_version(args.name, dsl_dict)
        print("\n✅ Initial DSL generated (with schema validation).")

    elif args.mode == "refine":
        if not args.hints:
            raise ValueError("Must provide --hints")
        if not args.crash_file:
            raise ValueError("Must provide --crash_file for refinement")

        crash_report = load_text(CRASH_REPORT_PATH + args.crash_file)

        dsl_dict = refine_dsl(args.name, args.hints, crash_report)

        save_new_version(args.name, dsl_dict)
        print("\n✅ DSL refined (schema-free evolution).")


if __name__ == "__main__":
    main()