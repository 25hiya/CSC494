# DSLinstanceToDSL/generator.py

import json
import ollama

from DSLinstanceToDSL.prompts import get_single_instance_prompt, get_multi_instance_prompt
from DSLinstanceToDSL.parser import GeneralizedDSLParser


class SchemaGenerator:
    def __init__(self, model: str = "llama3:8b"):
        self.model = model
        self.parser = GeneralizedDSLParser()

    def generate_schema(self, instances: dict[str, dict]) -> dict:
        """
        Generate a generalized DSL schema from one or more DSL instances.

        Args:
            instances: dict mapping instance name → DSL instance dict.
                       Pass a single-entry dict for single-instance mode.
        """
        if len(instances) == 1:
            (instance,) = instances.values()
            prompt_template = get_single_instance_prompt()
            prompt = prompt_template.format(
                dsl_instance=json.dumps(instance, indent=2)
            )
        else:
            prompt_template = get_multi_instance_prompt()
            instances_block = "\n\n".join(
                f"### Instance: {name}\n{json.dumps(inst, indent=2)}"
                for name, inst in instances.items()
            )
            prompt = prompt_template.format(dsl_instances=instances_block)

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )

        return self.parser.parse(response["message"]["content"])