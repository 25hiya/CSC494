# llm/prompt.py

from langchain_core.prompts import PromptTemplate

INITIAL_PROMPT = """
You are generating a JSON Schema representation of a crash report.

The crash report is the authoritative source of truth.
All values and structure must be grounded in the crash report.

Crash Report:
{crash_report}

IMPORTANT:
- Generate a valid JSON Schema.
- The schema must describe the structure and values inferred from the crash report.
- Do NOT invent facts not supported by the crash report.
- If a value is not explicitly stated, allow null.
- Do NOT return explanations.
- Do NOT return example data.
- Return ONLY the JSON Schema.

STRICT RULES:
- Output ONLY valid JSON.
- Wrap the JSON Schema in triple backticks.
- No explanations or extra text.

Required structure guidance:
{output_format}
"""


REFINE_PROMPT = """
You are refining an existing DSL instance describing a crash.

The crash report is the authoritative source of truth.
All modifications must be consistent with the crash report.

Crash Report:
{crash_report}

Existing DSL instance:
{previous_dsl}

Domain Expert Hints:
{hints}

IMPORTANT:
IMPORTANT:
- Update the JSON Schema according to the hints AND the crash report.
- Preserve correct schema structure.
- Do NOT invent facts.
- Do NOT return explanations.
- Do NOT include $schema, $defs, or $ref.
- Return ONLY the updated JSON Schema.

STRICT RULES:
- Preserve existing correct information.
- Apply only necessary modifications.
- Output ONLY valid JSON.
- Wrap JSON in triple backticks.
- No explanations.

Required structure:
{output_format}
"""


def get_initial_prompt(parser):
    return PromptTemplate(
        template=INITIAL_PROMPT,
        input_variables=["crash_report"],
        partial_variables={"output_format": parser.get_format_instructions()},
    )


def get_refine_prompt(parser):
    return PromptTemplate(
        template=REFINE_PROMPT,
        input_variables=["crash_report", "previous_dsl", "hints"],
        partial_variables={"output_format": parser.get_format_instructions()},
    )
