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


def generate_dsl(name: str, crash_report: str, domain_hints: str = ""):
    """
    Generate a DSL instance from a crash report.
    domain_hints optionally injects domain knowledge — this is the core research variable.
    """
    parser = get_parser(validate=False)
    llm = get_llm()
    prompt = get_initial_prompt(domain_hints=domain_hints)
    chain = prompt | llm

    if domain_hints:
        print(f"🧠 Domain hints injected ({len(domain_hints)} chars)")
    else:
        print("⚙️  L0 — no hints, LLM decides everything")

    dsl_obj = call_llm(chain, parser, {"crash_report": crash_report})
    if hasattr(dsl_obj, "model_dump"):
        return dsl_obj.model_dump()
    return dsl_obj


def refine_dsl(name: str, hints: str, crash_report: str):
    """
    Refine an existing DSL instance using correction hints.
    Requires a previously generated DSL saved under --name.
    """
    previous = load_previous_dsl(name)
    if previous is None:
        raise ValueError("No previous DSL found. Run generate first.")

    print(f"📝 Applying hints: {hints[:120]}...")

    parser = get_parser(validate=False)
    llm = get_llm()
    prompt = get_refine_prompt()
    chain = prompt | llm

    return call_llm(
        chain,
        parser,
        {
            "crash_report": crash_report,
            "previous_dsl": json.dumps(previous, indent=2),
            "hints": hints,
        },
    )


def main():
    parser = argparse.ArgumentParser(
        description="DSL generation and refinement pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
USAGE:

  # L0 — pure LLM, no domain hints
  python main.py --mode generate --name crash1_L0 --crash_file report1.txt

  # With domain hints
  python main.py --mode generate --name crash1_L1 --crash_file report1.txt --hints "hint text"

  # Refine an existing DSL instance
  python main.py --mode refine --name crash1_L0 --crash_file report1.txt --hints "correction text"
        """,
    )
    parser.add_argument("--mode", choices=["generate", "refine"], required=True)
    parser.add_argument("--name", type=str, required=True, help="Name for the DSL instance (used as filename)")
    parser.add_argument("--crash_file", type=str, required=True, help="Crash report filename inside CRASH_REPORT_PATH")
    parser.add_argument(
        "--hints",
        type=str,
        default="",
        help="Domain hints for generate mode, or correction hints for refine mode.",
    )

    args = parser.parse_args()
    crash_report = load_text(CRASH_REPORT_PATH + args.crash_file)

    if args.mode == "generate":
        dsl_dict = generate_dsl(args.name, crash_report, domain_hints=args.hints)
        save_new_version(args.name, dsl_dict)
        print("\n✅ DSL instance generated.")

    elif args.mode == "refine":
        if not args.hints:
            raise ValueError("--hints is required for refine mode.")
        dsl_dict = refine_dsl(args.name, args.hints, crash_report)
        save_new_version(args.name, dsl_dict)
        print("\n✅ DSL instance refined.")


if __name__ == "__main__":
    main()