
import json
import os
import threading
from datetime import datetime

HISTORY_FILE = "history.json"
_lock = threading.Lock()

DEFAULT_USER = {
    "conversations": [],
    "important_words": [],
    "mode": "normal",  # or "learning"
    "meta": {}
}


def _atomic_write(path: str, data: str):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
    os.replace(tmp, path)


def load_history() -> dict:
    """Load history from disk, migrate if necessary."""
    if not os.path.exists(HISTORY_FILE):
        return {}
    with _lock:
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            return {}

    migrated = migrate_history(raw)
    return migrated


def save_history(history: dict) -> None:
    """Save history atomically. Caller should supply a whole history dict."""
    with _lock:
        data = json.dumps(history, ensure_ascii=False, indent=4)
        _atomic_write(HISTORY_FILE, data)


def migrate_history(raw: dict) -> dict:
    """Auto-upgrade older formats to the new unified user object.

    Supported legacy formats:
      - user_id -> list (list of conversation dicts)
      - user_id -> { 'conversation': [...]}  (older variant)

    New format:
      user_id -> { 'conversations': [...], 'important_words': [...], 'mode': 'normal', 'meta': {...} }
    """
    if not isinstance(raw, dict):
        return {}

    out = {}
    for uid, value in raw.items():
        user_obj = {
            "conversations": [],
            "important_words": [],
            "mode": "normal",
            "meta": {}
        }
        # Case: legacy value is a list (direct conversations)
        if isinstance(value, list):
            user_obj["conversations"] = value
        elif isinstance(value, dict):
            # older key name could be 'conversation' or 'conversations'
            if "conversations" in value and isinstance(value["conversations"], list):
                user_obj["conversations"] = value["conversations"]
            elif "conversation" in value and isinstance(value["conversation"], list):
                user_obj["conversations"] = value["conversation"]
            else:
                # sometimes conversation entries are top-level list inside dict
                # fall back to scanning for list of dicts.
                for k, v in value.items():
                    if isinstance(v, list):
                        # assume first list is the conversation
                        user_obj["conversations"] = v
                        break

            # migrate important_words if existed
            if "important_words" in value and isinstance(value["important_words"], list):
                user_obj["important_words"] = value["important_words"]

            if "mode" in value and value["mode"] in ("normal", "learning"):
                user_obj["mode"] = value["mode"]

            if "meta" in value and isinstance(value["meta"], dict):
                user_obj["meta"] = value["meta"]
        else:
            # unknown shape, skip
            pass

        # ensure conversation is list of dicts with user/bot keys
        conv = []
        for item in user_obj["conversations"]:
            if isinstance(item, dict) and ("user" in item and "bot" in item):
                conv.append(item)

        user_obj["conversations"] = conv
        out[str(uid)] = user_obj

    return out


# Helper getters/setters (thread-safe wrappers)

def get_user(history: dict, user_id: str) -> dict:
    return history.setdefault(user_id, DEFAULT_USER.copy())


def touch_user(history: dict, user_id: str) -> dict:
    """Ensure user exists and return it."""
    if user_id not in history:
        history[user_id] = {
            "conversations": [],
            "important_words": [],
            "mode": "normal",
            "meta": {"created_at": datetime.utcnow().isoformat()}
        }
    return history[user_id]




# === FILE: README.md (short run notes) ===
# How to run
# 1. Put your real TOKEN and API_KEY into keys.py
# 2. Install deps: pip install pyTelegramBotAPI huggingface_hub
# 3. Run: python app.py

# Notes
# - Commands: /AddWords  -- add comma-separated words
#             /LearningOn -- enable learning chat
#             /LearningOff -- disable learning chat
# - The system will auto-migrate older history.json shapes to the new format on load.
# - history.json writes are atomic and thread-safe for single-process bots.
