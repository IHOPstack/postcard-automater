import json
import os

CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

CONFIG = load_config()

def get_setting(key, default=None):
    keys = key.split('.')
    value = CONFIG
    try:
        for k in keys:
            value = value[k]
        return value
    except KeyError:
        return default

def update_setting(key, value):
    if key in CONFIG.get('user_modifiable', {}):
        CONFIG['user_modifiable'][key] = value
        save_config(CONFIG)
    else:
        raise ValueError(f"Setting '{key}' is not user-modifiable")
