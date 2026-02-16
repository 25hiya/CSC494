# utils/file_io.py

import json
import os


def ensure_directory(path: str):
    os.makedirs(path, exist_ok=True)


def save_json(data: dict, path: str):
    ensure_directory(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
