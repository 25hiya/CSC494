import json
import re


class GeneralizedDSLParser:
    def parse(self, output: str):
        json_pattern = re.compile(r"```[^\n]*\n(.*?)\n```", re.DOTALL)
        match = json_pattern.search(output)

        if match:
            json_str = match.group(1)
        else:
            json_pattern = re.compile(r'\{.*\}', re.DOTALL)
            match = json_pattern.search(output)
            if match:
                json_str = match.group(0)
            else:
                raise ValueError("No valid JSON block found.")

        return json.loads(json_str)
