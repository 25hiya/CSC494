from langchain_core.prompts import PromptTemplate


GENERALIZE_PROMPT = """
You are generating a generalized DSL schema from a finalized DSL instance.

The DSL instance represents one specific crash.
Your task is to generalize it into a reusable domain-level DSL.

Final DSL Instance:
{dsl_instance}

IMPORTANT:
- Keep the same keys.
- Replace specific values with generalized representations.
- If the value is categorical → return a list of possible values.
- If the value is numeric → return the type (e.g., "number").
- If boolean → return ["true", "false"].
- Do NOT include explanations.
- Do NOT include examples.
- Return ONLY the generalized DSL.

STRICT RULES:
- Output ONLY valid JSON.
- Wrap output in triple backticks.
"""

def get_generalize_prompt():
    return PromptTemplate(
        template=GENERALIZE_PROMPT,
        input_variables=["dsl_instance"],
    )
