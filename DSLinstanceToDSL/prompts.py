# DSLinstanceToDSL/prompts.py

from langchain_core.prompts import PromptTemplate


# ── Single instance ────────────────────────────────────────────────────────────

SINGLE_INSTANCE_PROMPT = """
You are generating a generalized JSON schema from a single finalized JSON instance.

The JSON instance represents one specific crash.
Your task is to generalize it into a reusable domain-level JSON schema.

DSL Instance:
{dsl_instance}

RULES:
- Keep the same keys and structure.
- Replace specific values with generalized representations:
    - Categorical value  → list of plausible values, e.g. ["dry", "wet", "icy"]
    - Numeric value      → the string "number"
    - Boolean value      → ["true", "false"]
    - Free-text string   → the string "string"
    - Nested object      → recurse and generalize its fields
    - List of objects    → generalize one representative object
- Do NOT include explanations, comments, or examples.
- Output ONLY valid JSON wrapped in triple backticks.
"""


# ── Multiple instances ─────────────────────────────────────────────────────────

MULTI_INSTANCE_PROMPT = """
You are generating a unified generalized DSL schema from multiple finalized DSL instances.

Each instance represents one specific crash. Your task is to merge and generalize them
into a single reusable domain-level DSL schema that covers all instances.

DSL Instances:
{dsl_instances}

RULES:
- Produce ONE unified schema .
- Include every key that appears across the instance.
- Replace specific values with generalized representations:
    - Categorical value  → combined list of all observed values, e.g. ["dry", "wet", "icy"]
    - Numeric value      → the string "number"
    - Boolean value      → ["true", "false"]
    - Free-text string   → the string "string"
    - Nested object      → recurse and generalize its fields
    - List of objects    → generalize one representative object covering all variants
- Do NOT include explanations, comments, or examples.
- Output ONLY valid JSON wrapped in triple backticks.
"""


# ── Factories ──────────────────────────────────────────────────────────────────

def get_single_instance_prompt() -> PromptTemplate:
    return PromptTemplate(
        template=SINGLE_INSTANCE_PROMPT,
        input_variables=["dsl_instance"],
    )


def get_multi_instance_prompt() -> PromptTemplate:
    return PromptTemplate(
        template=MULTI_INSTANCE_PROMPT,
        input_variables=["dsl_instances"],
    )