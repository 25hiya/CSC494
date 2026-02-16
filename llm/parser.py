# llm/parser.py

import json
import re
from langchain_core.output_parsers import PydanticOutputParser
from dsl.schema import DSL


class ValidatingJSONDSLParser(PydanticOutputParser):
    """Parser that validates against Pydantic schema."""
    
    def parse(self, output: str):
        # Extract JSON from code blocks or raw text
        json_pattern = re.compile(r"```[^\n]*\n(.*?)\n```", re.DOTALL)
        match = json_pattern.search(output)

        if match:
            json_str = match.group(1)
        else:
            # Try to find raw JSON
            json_pattern = re.compile(r'\{.*\}', re.DOTALL)
            match = json_pattern.search(output)
            if match:
                json_str = match.group(0)
            else:
                raise ValueError("No valid JSON block found.")
        
        # Parse and validate with Pydantic
        json_object = json.loads(json_str)
        return self._parse_obj(json_object)


class SchemaFreeJSONParser:
    """Parser that returns raw dict without schema validation."""
    
    def parse(self, output: str):
        # Extract JSON from code blocks or raw text
        json_pattern = re.compile(r"```[^\n]*\n(.*?)\n```", re.DOTALL)
        match = json_pattern.search(output)

        if match:
            json_str = match.group(1)
        else:
            # Try to find raw JSON
            json_pattern = re.compile(r'\{.*\}', re.DOTALL)
            match = json_pattern.search(output)
            if match:
                json_str = match.group(0)
            else:
                raise ValueError("No valid JSON block found.")
        
        # Parse JSON and return raw dict (no validation)
        json_object = json.loads(json_str)
        return json_object
    
    def get_format_instructions(self):
        """Return format instructions for the LLM."""
        return """Return a valid JSON object wrapped in triple backticks.

Example:
````json
{
  "field": "value"
}
```"""


def get_parser(validate=True):
    """
    Get parser with optional validation.
    
    Args:
        validate: If True, validates against DSL schema. If False, returns raw dict.
    """
    if validate:
        return ValidatingJSONDSLParser(pydantic_object=DSL)
    else:
        return SchemaFreeJSONParser()