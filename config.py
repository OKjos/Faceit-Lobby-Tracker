"""
config.py
---------
Saves and loads the user's nickname, player ID, and API key to a JSON file
in their home directory (~/.faceit_companion.json).

This means the user only has to enter their info once — it's remembered
between app restarts.
"""

import json
import os

# File path: C:\Users\YourName\.faceit_companion.json
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".faceit_companion.json")


def load_config():
    """Read saved config. Returns a dict or None if no config exists yet."""
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None


def save_config(config):
    """
    Write config to disk.
    Pass None to delete the saved config (used on logout).
    """
    if config is None:
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        return
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
