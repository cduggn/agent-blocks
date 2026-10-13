# Verifier contract

A verifier proves a named behavior. A skill explains how to run it; an executable check or observed interaction supplies the evidence. Keep one project registry at `verification/registry.json`, or use the project's existing equivalent.

## Registry entries

Each entry has a unique ID, shared or project scope, applicable task kinds or surfaces, the claim it can prove, the command or procedure path, prerequisites, expected result, timeout, evidence location, and cleanup steps. Task acceptance criteria explicitly select required verifier IDs; automatic file matching can suggest checks but cannot silently remove required ones.

For example, this entry describes an illustrative application check. Replace its command with one actually supported by the chosen application before registering it:

```json
{
  "id": "export-retry",
  "scope": "project",
  "applies_to": ["export"],
  "claim": "Retrying an export writes one row per record",
  "command": ["python", "-m", "pytest", "tests/test_export_retry.py"],
  "prerequisites": ["Project test dependencies installed"],
  "expected": "Zero exit status and assertions covering row counts after retry",
  "timeout_seconds": 120,
  "evidence": ".artifacts/verification/<task-id>/<run-id>/export-retry.log",
  "cleanup": "Test fixtures remove their temporary export files"
}
```

Reusable shared verifiers can check formatting or defined architectural invariants. Their commands still need project configuration. Project verifiers exercise application behavior: retry semantics, API authorization, UI persistence, or diagnostic quality. A static check is not a substitute for an application outcome.

## Result and completion rule

Record verifier ID, task/run ID, status (`pass`, `fail`, `blocked`, or `not_applicable`), tested commit plus dirty-diff/snapshot identity, command/procedure, exit status where relevant, expected and observed outcome, artifact paths, and limitations. Distinguish simulated external services from live integration evidence.

Missing registration, missing prerequisites, timeout, unavailable evidence, and a check never run cannot count as pass. A required check marked not_applicable cannot satisfy acceptance; resolve the task's requirement explicitly. All required checks and all acceptance outcomes need current evidence before completion.

## Command runner

The bundled `scripts/verify.py` supports macOS/Linux and Python 3.9+. Run it from any directory using absolute input paths, or from the project root with relative paths:

```bash
python3 /path/to/task-worker/scripts/verify.py \
  --project /path/to/project \
  --task /path/to/task-verification.json \
  --registry /path/to/project/verification/registry.json \
  --output /tmp/project-verification
```

The task JSON needs an `id`, a nonempty `sources` list of project-relative files, and an `acceptance` list. Each criterion has an `id`, an `outcome`, and a nonempty `verifiers` list. The registry is an object with a `verifiers` list; each entry requires `id`, `scope`, `claim`, `command` (argument array), and positive finite `timeout_seconds`. Other entry fields document the recipe. Source lists should include implementation, checks, and relevant configuration. The report fingerprints only these declared files; it does not claim whole-repository coverage.

The runner executes commands sequentially with the project as the working directory. Each command must assert its own expected behavior, return nonzero on failure, and perform its fixture cleanup. The runner does not interpret prose expectations, prerequisites, or cleanup fields. It captures combined output in per-check logs, stops the command's process group after a timeout or exit, and preserves evidence in a unique run directory. Use self-contained command checks; interactive services need a wrapper that starts, exercises, and tears down its own instance. Only run registry commands from a project whose execution is within the task's authorization.

Exit 0 means every selected command passed and declared source/task/registry fingerprints matched before and after the run. Run in an isolated workspace without concurrent writers; endpoint fingerprints cannot detect transient edits that are reverted. Exit 1 means a check failed. Exit 2 means blocked or invalid input, including a missing registration, unavailable command, timeout, or changed input. Invalid configuration is reported on stderr before execution. The runner rejects duplicate IDs and empty acceptance/check lists. It saves task/registry snapshots and fingerprints alongside results; each invocation reruns checks instead of reusing a prior report.

This enforces the command-verification gate, not task-store permissions or final closure. There is no automatic acceptance assessor or task closer. Human/interactive review remains a separate requirement where the task calls for it. Before closing later, rerun if relevant sources or requirements changed; a saved report is evidence of that run only.

## Add one verifier at a time

1. Choose a real acceptance criterion and reuse a suitable existing check or control harness.
2. Add its registry entry and project-local procedure. For interactive applications, establish launch, health check, drive, evidence, cleanup, and a feature map. The optional upstream verifier skills linked in the repository README provide examples.
3. Run against known-good behavior and a representative failure in a disposable environment; confirm the latter is detected. Preserve proof through cleanup.
4. Reference the ID from a real task and execute the whole task loop.
5. When behavior changes, maintain the check and feature map together. Keep its scope of proof explicit.

Before unattended execution, connect the runner's fresh result to the dispatcher or CI completion gate and test that task closure rejects failed, missing, and stale proof. Do not allow the implementation worker to weaken acceptance criteria merely to obtain a pass.
