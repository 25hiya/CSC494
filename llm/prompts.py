# llm/prompts.py

from langchain_core.prompts import PromptTemplate


# ── Generation prompt ─────────────────────────────────────────────────────────
# No schema. No structure. No keys. The LLM decides everything.
# {domain_context} is empty at L0. Domain hints are injected at higher levels.

INITIAL_PROMPT = """
You are a domain expert in road traffic crashes.

Read the following crash report and represent it as a structured JSON object.
Decide the structure yourself — choose whatever keys, nesting, and organisation
best captures the information in the crash report.

Crash Report:
{crash_report}

{domain_context}

Output ONLY a valid JSON object wrapped in triple backticks. No explanations.
"""


# ── Refine prompt ─────────────────────────────────────────────────────────────

REFINE_PROMPT = """
You are refining a JSON representation of a crash.

The crash report is the authoritative source of truth.

Crash Report:
{crash_report}

Current JSON:
{previous_dsl}

Refinement Instructions:
{hints}

RULES:
- Apply the refinement instructions precisely.
- Preserve all correct existing values.
- Do NOT invent values not in the crash report.
- Output ONLY the updated JSON object wrapped in triple backticks. No explanations.
"""


# ── Auto-critique prompt ──────────────────────────────────────────────────────

AUTO_CRITIQUE_PROMPT = """
You are reviewing a JSON representation of a crash report for accuracy and completeness.

Crash Report (ground truth):
{crash_report}

Current JSON:
{dsl_instance}

{domain_context}

Check for:
1. Information present in the crash report that is missing from the JSON
2. Values in the JSON that contradict the crash report
3. speed or numeric values that were guessed rather than taken from the report

If the JSON accurately and completely represents the crash report, output exactly: NO_ISSUES

Otherwise output:
```json
{
  "issues": [
    {
      "field": "<path to the field>",
      "problem": "<what is wrong>",
      "fix": "<what it should be>"
    }
  ]
}
```

Output ONLY the JSON or NO_ISSUES. No explanations.
"""


HINTS_FROM_ISSUES_PROMPT = """
Convert this list of JSON issues into a single concise refinement instruction paragraph.
Be specific about field paths and correct values.

Issues:
{issues_json}

Write one plain-text paragraph. No JSON, no bullet points, no preamble.
"""


# ── Factories ─────────────────────────────────────────────────────────────────

def get_initial_prompt(parser=None, domain_hints: str = ""):
    domain_context = (
        f"Domain Context:\n{domain_hints}"
        if domain_hints.strip()
        else ""
    )
    return PromptTemplate(
        template=INITIAL_PROMPT,
        input_variables=["crash_report"],
        partial_variables={"domain_context": domain_context},
    )


def get_refine_prompt(parser=None):
    return PromptTemplate(
        template=REFINE_PROMPT,
        input_variables=["crash_report", "previous_dsl", "hints"],
    )


def get_critique_prompt(domain_hints: str = ""):
    domain_context = (
        f"Additional domain context to apply during review:\n{domain_hints}"
        if domain_hints.strip()
        else ""
    )
    return PromptTemplate(
        template=AUTO_CRITIQUE_PROMPT,
        input_variables=["crash_report", "dsl_instance"],
        partial_variables={"domain_context": domain_context},
    )


def get_hints_from_issues_prompt():
    return PromptTemplate(
        template=HINTS_FROM_ISSUES_PROMPT,
        input_variables=["issues_json"],
    )