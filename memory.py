"""Simple persistent memory: past tasks, stored in memory.json."""
import json
import os

PATH = os.path.join(os.path.dirname(__file__), "..", "memory.json")


def load() -> list:
    if os.path.exists(PATH):
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def add(entry: str) -> None:
    items = load()
    items.append(entry)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(items[-20:], f, indent=2)  # keep last 20
