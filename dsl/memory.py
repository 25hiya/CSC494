# dsl/memory.py

import os
from datetime import datetime
from utils.files_io import save_json, load_json
from config import DATA_PATH


def get_dsl_path(name: str):
    return os.path.join(DATA_PATH, f"{name}.json")


def load_previous_dsl(name: str):
    path = get_dsl_path(name)
    if os.path.exists(path):
        return load_json(path)
    return None


def save_new_version(name: str, dsl_dict: dict):
    dsl_dict["metadata"]["last_updated"] = datetime.utcnow().isoformat()
    path = get_dsl_path(name)
    save_json(dsl_dict, path)
