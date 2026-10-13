"""The step 1 system prompt names every field and hint, and quotes no test brief (Task 4)."""

import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT = (ROOT / "shared" / "prompts" / "step1.system.md").read_text(encoding="utf-8")
CONTRACT = json.loads((ROOT / "shared" / "contracts" / "step1.output.schema.json").read_text())
BRIEFS = tomllib.loads((ROOT / "evals" / "recipe_briefs.toml").read_text(encoding="utf-8"))["brief"]
WORDINGS = tomllib.loads((ROOT / "evals" / "role_wordings.toml").read_text(encoding="utf-8"))["wording"]


def _words(text: str) -> list[str]:
    return re.findall(r"[\w'-]+", text.lower())


def test_prompt_names_every_output_field():
    for field in CONTRACT["properties"]:
        assert f"`{field}`" in PROMPT, field


def test_prompt_names_every_hint_word():
    for hint in CONTRACT["properties"]["hints"]["items"]["enum"]:
        assert f"`{hint}`" in PROMPT, hint


def test_prompt_names_every_stated_number():
    for key in CONTRACT["properties"]["stated"]["properties"]:
        assert f"`{key}`" in PROMPT, key


def test_prompt_quotes_no_brief():
    prompt = " ".join(_words(PROMPT))
    for brief in BRIEFS:
        words = _words(brief["request"])
        for i in range(len(words) - 4):
            run = " ".join(words[i:i + 5])
            assert run not in prompt, f"{brief['id']}: {run}"


def test_prompt_quotes_no_role_wording():
    prompt = " ".join(_words(PROMPT))
    for wording in WORDINGS:
        words = _words(wording["request"])
        for i in range(len(words) - 4):
            run = " ".join(words[i:i + 5])
            assert run not in prompt, f"{wording['id']}: {run}"
