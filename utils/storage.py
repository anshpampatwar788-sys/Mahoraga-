import json
import os

# Use Railway's persistent volume if it exists, otherwise fall back to the
# local data/ folder so the bot works the same in both environments.
_RAILWAY_VOLUME = "/app/data"
_LOCAL_DATA = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
BASE_DIR = _RAILWAY_VOLUME if os.path.exists(_RAILWAY_VOLUME) else _LOCAL_DATA

# Make sure the directory always exists (matters for first local run).
os.makedirs(BASE_DIR, exist_ok=True)

DATA_PATH = os.path.join(BASE_DIR, "economy.json")
BIRTHDAY_PATH = os.path.join(BASE_DIR, "birthdays.json")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
REWARDS_PATH = os.path.join(BASE_DIR, "rewards.json")


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


# --- Reward Shop ---
# rewards.json shape:
# {
#   "items": {"1": {"id": 1, "name": ..., "description": ..., "cost": ...,
#                    "stock": int|null, "enabled": bool, "category": str}, ...},
#   "next_item_id": int,
#   "redemptions": {"<user_id>": [{"redemption_id": "RW-0001", "item_id": 1,
#                                   "item_name": ..., "cost": ..., "timestamp": iso,
#                                   "claimed": bool}, ...]},
#   "next_redemption_number": int
# }

def _load_rewards() -> dict:
    data = _load(REWARDS_PATH)
    data.setdefault("items", {})
    data.setdefault("next_item_id", 1)
    data.setdefault("redemptions", {})
    data.setdefault("next_redemption_number", 1)
    return data


def _save_rewards(data: dict):
    _save(REWARDS_PATH, data)


def add_reward_item(name: str, description: str, cost: int, stock=None, category: str = "General") -> dict:
    data = _load_rewards()
    item_id = data["next_item_id"]
    item = {
        "id": item_id,
        "name": name,
        "description": description,
        "cost": cost,
        "stock": stock,  # None = unlimited
        "enabled": True,
        "category": category,
    }
    data["items"][str(item_id)] = item
    data["next_item_id"] = item_id + 1
    _save_rewards(data)
    return item


def edit_reward_item(item_id: int, **fields) -> dict:
    """Update any subset of name/description/cost/stock/category on an existing item."""
    data = _load_rewards()
    item = data["items"].get(str(item_id))
    if not item:
        return None
    for key, value in fields.items():
        if value is not None and key in ("name", "description", "cost", "stock", "category"):
            item[key] = value
    _save_rewards(data)
    return item


def remove_reward_item(item_id: int) -> bool:
    data = _load_rewards()
    if str(item_id) in data["items"]:
        del data["items"][str(item_id)]
        _save_rewards(data)
        return True
    return False


def set_reward_stock(item_id: int, stock) -> dict:
    """stock can be an int, or None for unlimited."""
    return edit_reward_item(item_id, stock=stock)


def toggle_reward_item(item_id: int) -> dict:
    data = _load_rewards()
    item = data["items"].get(str(item_id))
    if not item:
        return None
    item["enabled"] = not item["enabled"]
    _save_rewards(data)
    return item


def get_reward_item(item_id: int) -> dict:
    data = _load_rewards()
    return data["items"].get(str(item_id))


def get_all_reward_items(enabled_only: bool = False) -> list:
    data = _load_rewards()
    items = list(data["items"].values())
    if enabled_only:
        items = [i for i in items if i.get("enabled", True)]
    items.sort(key=lambda i: (i.get("category", ""), i["cost"]))
    return items


def decrement_reward_stock(item_id: int) -> bool:
    """Decrements stock by 1 if limited. Returns False if out of stock, True otherwise
    (including unlimited-stock items, which always return True)."""
    data = _load_rewards()
    item = data["items"].get(str(item_id))
    if not item:
        return False
    if item.get("stock") is None:
        return True
    if item["stock"] <= 0:
        return False
    item["stock"] -= 1
    _save_rewards(data)
    return True


def create_redemption(user_id: int, item: dict) -> dict:
    data = _load_rewards()
    number = data["next_redemption_number"]
    redemption_id = f"RW-{number:04d}"
    import datetime
    record = {
        "redemption_id": redemption_id,
        "item_id": item["id"],
        "item_name": item["name"],
        "cost": item["cost"],
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "claimed": False,
    }
    data["redemptions"].setdefault(str(user_id), []).append(record)
    data["next_redemption_number"] = number + 1
    _save_rewards(data)
    return record


def get_user_redemptions(user_id: int) -> list:
    data = _load_rewards()
    return data["redemptions"].get(str(user_id), [])


def mark_redemption_claimed(user_id: int, redemption_id: str) -> bool:
    data = _load_rewards()
    for record in data["redemptions"].get(str(user_id), []):
        if record["redemption_id"] == redemption_id:
            record["claimed"] = True
            _save_rewards(data)
            return True
    return False
