"""Tools the agent can call. Each tool has a JSON schema + a Python implementation."""
import ast
import datetime
import operator
import os
import requests

NOTES_DIR = os.path.join(os.path.dirname(__file__), "..", "notes")
os.makedirs(NOTES_DIR, exist_ok=True)

TOOL_SCHEMAS = [
    {
        "name": "wikipedia_search",
        "description": "Search Wikipedia and return a short summary of the best-matching article. Use for factual lookups.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Topic to look up"}},
            "required": ["query"],
        },
    },
    {
        "name": "calculator",
        "description": "Evaluate an arithmetic expression, e.g. '(12*7)/3 + 2**4'.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
    {
        "name": "current_datetime",
        "description": "Get the current date and time.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "save_note",
        "description": "Save text to a named note file (long-term storage). Use to store the final report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Short file name without extension"},
                "content": {"type": "string"},
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "list_notes",
        "description": "List all saved notes.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_note",
        "description": "Read a saved note by title.",
        "input_schema": {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "required": ["title"],
        },
    },
]

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv,
}


def _eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    return str(_eval(ast.parse(expression, mode="eval").body))  # safe: no eval()


def wikipedia_search(query: str) -> str:
    headers = {"User-Agent": "research-agent/1.0 (student project)"}
    r = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 1},
        headers=headers, timeout=15,
    )
    hits = r.json()["query"]["search"]
    if not hits:
        return "No results found."
    title = hits[0]["title"]
    s = requests.get(
        f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
        headers=headers, timeout=15,
    ).json()
    return f"{s.get('title')}: {s.get('extract', 'No summary.')}"


def current_datetime() -> str:
    return datetime.datetime.now().strftime("%A, %d %B %Y, %H:%M")


def _safe(title: str) -> str:
    return "".join(c for c in title if c.isalnum() or c in "-_ ").strip().replace(" ", "_")


def save_note(title: str, content: str) -> str:
    path = os.path.join(NOTES_DIR, _safe(title) + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Saved to {os.path.basename(path)}"


def list_notes() -> str:
    files = [f for f in os.listdir(NOTES_DIR) if f.endswith(".md")]
    return "\n".join(files) if files else "No notes yet."


def read_note(title: str) -> str:
    path = os.path.join(NOTES_DIR, _safe(title) + ".md")
    if not os.path.exists(path):
        return "Note not found."
    with open(path, encoding="utf-8") as f:
        return f.read()


REGISTRY = {
    "wikipedia_search": wikipedia_search, "calculator": calculator,
    "current_datetime": current_datetime, "save_note": save_note,
    "list_notes": list_notes, "read_note": read_note,
}


def run_tool(name: str, args: dict) -> str:
    try:
        return REGISTRY[name](**args)
    except Exception as e:  # errors go back to the LLM so it can recover
        return f"Tool error: {e}"
