from typing import List, Tuple
from .history_manager import get_user, touch_user, save_history, load_history


def _normalize(w: str) -> str:
    return w.strip()


def add_words(user_id: str, raw_words: str) -> Tuple[int, int]:
    """Add comma-separated words. Returns (added_count, duplicate_count)."""
    history = load_history()
    user = touch_user(history, user_id)

    pieces = [p.strip() for p in raw_words.split(",") if p.strip()]
    existing = {w for w in user.get("important_words", [])}
    added = 0
    duplicates = 0
    for p in pieces:
        n = _normalize(p)
        if not n:
            continue
        if n in existing:
            duplicates += 1
        else:
            user.setdefault("important_words", []).append(n)
            existing.add(n)
            added += 1

    save_history(history)
    return added, duplicates


def list_words(user_id: str) -> List[str]:
    history = load_history()
    user = get_user(history, user_id)
    return user.get("important_words", [])


def remove_words(user_id: str, raw_words: str) -> int:
    history = load_history()
    user = touch_user(history, user_id)
    pieces = [p.strip() for p in raw_words.split(",") if p.strip()]
    existing = set(user.get("important_words", []))
    removed = 0
    for p in pieces:
        n = _normalize(p)
        if n in existing:
            existing.remove(n)
            removed += 1
    user["important_words"] = list(existing)
    save_history(history)
    return removed


