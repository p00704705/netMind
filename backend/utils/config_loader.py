import os
import json


def get_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "..", "config", "tool_config.json")
    with open(config_path) as f:
        config = json.load(f)
    return config
