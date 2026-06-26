import json
import os

BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_PATH = os.path.join(BASE_DIR, "economy.json")
BIRTHDAY_PATH = os.path.join(BASE_DIR, "birthdays.json")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")


def _load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# --- Economy ---

def get_balance(user_id: int) -> int:
    data = _load(DATA_PATH)
    return data.get(str(user_id), {}).get("balance", 0)


def set_balance(user_id: int, amount: int):
    data = _load(DATA_PATH)
    data.setdefault(str(user_id), {})["balance"] = max(0, amount)
    _save(DATA_PATH, data)


def add_balance(user_id: int, amount: int) -> int:
    new_balance = max(0, get_balance(user_id) + amount)
    set_balance(user_id, new_balance)
    return new_balance


def get_last_daily(user_id: int):
    data = _load(DATA_PATH)
    return data.get(str(user_id), {}).get("last_daily")


def set_last_daily(user_id: int, iso_timestamp: str):
    data = _load(DATA_PATH)
    data.setdefault(str(user_id), {})["last_daily"] = iso_timestamp
    _save(DATA_PATH, data)


def get_leaderboard(limit: int = 10):
    data = _load(DATA_PATH)
    entries = [(int(uid), info.get("balance", 0)) for uid, info in data.items()]
    entries.sort(key=lambda x: x[1], reverse=True)
    return entries[:limit]


def reset_all_balances():
    data = _load(DATA_PATH)
    for uid in data:
        data[uid]["balance"] = 0
    _save(DATA_PATH, data)


# --- Birthdays ---

def set_birthday(user_id: int, month: int, day: int):
    data = _load(BIRTHDAY_PATH)
    data[str(user_id)] = {"month": month, "day": day}
    _save(BIRTHDAY_PATH, data)


def get_birthday(user_id: int):
    data = _load(BIRTHDAY_PATH)
    return data.get(str(user_id))


def get_all_birthdays() -> dict:
    return _load(BIRTHDAY_PATH)


# --- Server config (e.g. announcement channel IDs) ---

def get_config(key: str, default=None):
    data = _load(CONFIG_PATH)
    return data.get(key, default)


def set_config(key: str, value):
    data = _load(CONFIG_PATH)
    data[key] = value
    _save(CONFIG_PATH, data)
