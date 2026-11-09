"""Gemini-powered Research Agent: Plan -> Act -> Observe -> Reflect."""
import os
import requests
from dotenv import load_dotenv
from . import memory
from .tools import TOOL_SCHEMAS, run_tool

load_dotenv()
MODEL = os.getenv("MODEL", "gemini-2.5-flash")
MAX_STEPS = 10
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SYSTEM = """You are an autonomous Research Agent.
Workflow for every task:
1. PLAN: write a short numbered plan before using tools.
2. ACT: call tools (wikipedia_search, calculator, current_datetime, notes tools) as needed.
3. OBSERVE: read each result; if a tool fails or is unhelpful, adapt and try another approach.
4. FINISH: give a clear final answer, and save a report with save_note when the user asks for research.
Never invent facts; use tools to verify. Stop as soon as the goal is met.

Long-term memory from earlier sessions:
{memory}
"""


def _gemini_tools():
    declarations = []
    for tool in TOOL_SCHEMAS:
        declarations.append({
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["input_schema"],
        })
    return [{"functionDeclarations": declarations}]


class ResearchAgent:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key or self.api_key == "your_key_here":
            raise RuntimeError("GEMINI_API_KEY is missing. Add your Google AI Studio key to the .env file.")
        self.contents = []

    def run(self, goal: str, verbose: bool = True) -> str:
        mem = "\n".join(f"- {m}" for m in memory.load()) or "(empty)"
        system = SYSTEM.format(memory=mem)
        self.contents.append({"role": "user", "parts": [{"text": goal}]})
        headers = {"Content-Type": "application/json"}

        for step in range(1, MAX_STEPS + 1):
            payload = {
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": self.contents,
                "tools": _gemini_tools(),
                "toolConfig": {"functionCallingConfig": {"mode": "AUTO"}},
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1800},
            }
            response = requests.post(
                API_URL.format(model=MODEL), params={"key": self.api_key},
                headers=headers, json=payload, timeout=90,
            )
            if not response.ok:
                try:
                    detail = response.json().get("error", {}).get("message", response.text)
                except Exception:
                    detail = response.text
                raise RuntimeError(f"Gemini API error ({response.status_code}): {detail}")

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError(f"Gemini returned no candidates: {data}")
            model_content = candidates[0].get("content", {"role": "model", "parts": []})
            parts = model_content.get("parts", [])
            self.contents.append(model_content)

            calls = [p["functionCall"] for p in parts if "functionCall" in p]
            for part in parts:
                if "text" in part and part["text"].strip() and verbose:
                    print(f"\n[Step {step}] Thought: {part['text'].strip()}")

            if not calls:
                final = "\n".join(p.get("text", "") for p in parts if p.get("text"))
                memory.add(f"Task: {goal[:100]} -> done")
                return final or "The model returned no text answer."

            function_responses = []
            for call in calls:
                name = call.get("name", "")
                args = call.get("args", {}) or {}
                if verbose:
                    print(f"[Step {step}] Action: {name}({args})")
                out = run_tool(name, args)
                if verbose:
                    print(f"[Step {step}] Observation: {out[:200]}")
                function_responses.append({
                    "functionResponse": {"name": name, "response": {"result": out}}
                })
            self.contents.append({"role": "user", "parts": function_responses})

        return "Stopped: reached the maximum number of steps."
