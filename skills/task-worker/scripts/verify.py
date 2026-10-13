#!/usr/bin/env python3
"""Run the required command verifiers for one task; never close the task."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value)


def read_json(path):
    raw = Path(path).read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def source_hashes(project, paths):
    hashes = {}
    for name in paths:
        require(isinstance(name, str), "Source paths must be strings")
        path = (project / name).resolve()
        require(path.is_relative_to(project), f"Source escapes project: {name}")
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def run_check(entry, project, directory):
    log = directory / (entry["id"] + ".log")
    result = {"id": entry["id"], "command": entry["command"],
              "claim": entry["claim"], "log": str(log), "exit_code": None}
    with log.open("wb") as output:
        try:
            process = subprocess.Popen(entry["command"], cwd=project, stdout=output,
                                       stderr=subprocess.STDOUT, start_new_session=True)
        except OSError as error:
            result.update(status="blocked", reason=str(error))
            return result
        try:
            result["exit_code"] = process.wait(timeout=entry["timeout_seconds"])
            result["status"] = "pass" if result["exit_code"] == 0 else "fail"
        except subprocess.TimeoutExpired:
            result.update(status="blocked", reason="Verifier timed out")
        finally:
            # Command verifiers must finish their children before returning.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    return result


def verify(project, task_path, registry_path, output_root):
    task, task_hash = read_json(task_path)
    registry, registry_hash = read_json(registry_path)
    require(isinstance(task, dict) and identifier(task.get("id")), "Task needs a valid id")
    criteria = task.get("acceptance")
    require(isinstance(criteria, list) and criteria, "Task needs acceptance criteria")
    required = []
    criterion_ids = set()
    for criterion in criteria:
        require(isinstance(criterion, dict) and identifier(criterion.get("id")),
                "Each acceptance criterion needs an id")
        require(criterion["id"] not in criterion_ids, "Duplicate acceptance id")
        criterion_ids.add(criterion["id"])
        require(isinstance(criterion.get("outcome"), str) and criterion["outcome"].strip(),
                "Each acceptance criterion needs an outcome")
        ids = criterion.get("verifiers")
        require(isinstance(ids, list) and ids and all(identifier(i) for i in ids),
                "Every acceptance criterion needs verifier ids")
        required.extend(ids)
    require(isinstance(registry, dict) and isinstance(registry.get("verifiers"), list),
            "Registry needs a verifiers list")
    entries = {}
    for entry in registry["verifiers"]:
        require(isinstance(entry, dict) and identifier(entry.get("id")), "Invalid verifier id")
        require(entry["id"] not in entries, "Duplicate verifier id")
        require(entry.get("scope") in ("shared", "project"), "Invalid verifier scope")
        command = entry.get("command")
        require(isinstance(command, list) and command and
                all(isinstance(arg, str) and arg for arg in command), "Command needs an argv list")
        require(isinstance(entry.get("claim"), str) and entry["claim"].strip(), "Missing verifier claim")
        timeout = entry.get("timeout_seconds")
        require(type(timeout) in (int, float) and math.isfinite(timeout) and timeout > 0,
                "Timeout must be positive and finite")
        entries[entry["id"]] = entry
    paths = task.get("sources")
    require(isinstance(paths, list) and paths, "Task needs source files to fingerprint")
    before = source_hashes(project, paths)
    output_root.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix=task["id"] + "-", dir=output_root))
    report = {"task_id": task["id"], "project": str(project),
              "started_at": datetime.now(timezone.utc).isoformat(),
              "task_sha256": task_hash, "registry_sha256": registry_hash,
              "sources_before": before, "acceptance": criteria, "results": []}
    (directory / "task.json").write_text(json.dumps(task, indent=2) + "\n")
    (directory / "registry.json").write_text(json.dumps(registry, indent=2) + "\n")
    for verifier_id in dict.fromkeys(required):
        entry = entries.get(verifier_id)
        report["results"].append(run_check(entry, project, directory) if entry else
                                 {"id": verifier_id, "status": "blocked", "reason": "Missing registration"})
    try:
        report["sources_after"] = source_hashes(project, paths)
        unchanged = report["sources_after"] == before
        unchanged = unchanged and read_json(task_path)[1] == task_hash
        unchanged = unchanged and read_json(registry_path)[1] == registry_hash
    except (OSError, ValueError):
        unchanged = False
    report["inputs_unchanged"] = unchanged
    report["status"] = "pass" if unchanged and all(
        r["status"] == "pass" for r in report["results"]) else "blocked" if (
        not unchanged or any(r["status"] == "blocked" for r in report["results"])) else "fail"
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report_path = directory / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report, report_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report, path = verify(args.project.resolve(), args.task.resolve(),
                              args.registry.resolve(), args.output.resolve())
    except (OSError, ValueError, TypeError) as error:
        print(f"blocked: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "report": str(path)}))
    return {"pass": 0, "fail": 1, "blocked": 2}[report["status"]]


if __name__ == "__main__":
    sys.exit(main())
