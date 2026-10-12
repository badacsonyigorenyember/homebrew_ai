"""Export the n8n workflows into n8n/workflows/ so they are versioned with the repo.

Run `python -m evals.workflows` after every workflow change.
"""

import json
import re
import subprocess
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent / "n8n" / "workflows"
# n8n sees ./shared as /data/shared; files written there are root-owned (OPERATIONS §5)
SHARED_DIR = Path(__file__).resolve().parent.parent / "shared"
CONTAINER_FILE = "/data/shared/.n8n-export.json"
KEEP = ("id", "name", "nodes", "connections", "settings")


def export_all() -> list[dict]:
    """All workflows in n8n. stdout carries log lines, so export to a file and read that."""
    run = subprocess.run(
        ["docker", "exec", "n8n", "n8n", "export:workflow", "--all", "--pretty",
         f"--output={CONTAINER_FILE}"],
        capture_output=True, text=True,
    )
    host_file = SHARED_DIR / ".n8n-export.json"
    try:
        if not host_file.exists():
            if "No workflows found" in run.stdout + run.stderr:
                return []
            raise RuntimeError(f"n8n export failed: {run.stdout}{run.stderr}")
        return json.loads(host_file.read_text())
    finally:
        subprocess.run(["docker", "exec", "n8n", "rm", "-f", CONTAINER_FILE],
                       capture_output=True)


def shape(workflow: dict) -> dict:
    """Keep only what changes when the workflow changes."""
    return {k: workflow[k] for k in KEEP if k in workflow}


def file_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") + ".json"


def node_graph(workflow: dict) -> tuple[set[str], dict]:
    return {n["name"] for n in workflow["nodes"]}, workflow["connections"]


def main() -> None:
    REPO_DIR.mkdir(parents=True, exist_ok=True)
    for wf in export_all():
        path = REPO_DIR / file_name(wf["name"])
        path.write_text(json.dumps(shape(wf), indent=2, ensure_ascii=False) + "\n")
        print(path)


if __name__ == "__main__":
    main()
