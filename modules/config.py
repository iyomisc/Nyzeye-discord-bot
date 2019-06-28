"""
Common config instance
"""

import json


with open("config.json", "r") as f:
    CONFIG = json.load(f)

with open("shortcuts.json", "r") as f:
    SHORTCUTS = json.load(f)
