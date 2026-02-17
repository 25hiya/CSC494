import ollama
from DSLinstanceToDSL.prompts import get_generalize_prompt
from DSLinstanceToDSL.parser import GeneralizedDSLParser


class SchemaGenerator:
    def __init__(self, model="llama3:8b"):
        self.model = model
        self.parser = GeneralizedDSLParser()

    def generate_schema(self, dsl_instance: str):
        prompt = get_generalize_prompt().format(
            dsl_instance=dsl_instance
        )

        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return self.parser.parse(response["message"]["content"])
