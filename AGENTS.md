# Working on Agent Blocks

Keep this framework modular and understandable. The worker skill describes the workflow; the runner executes command verifiers; task storage and dispatch are separate integration blocks.

- Runtime: Python 3.9+ on macOS or Linux, standard library only.
- Run behavioral tests with `python3 tests/test_verify.py`.
- Run the full pilot from the repository root:

```bash
python3 skills/task-worker/scripts/verify.py --project . --task examples/task.json --registry examples/registry.json --output /tmp/agent-blocks-verification
```

Register verifiers in a project's registry and select them through task acceptance criteria. Keep application-specific commands with their application. Extend tests when changes affect rejection of failed, missing, timed-out, or stale proof. Never weaken acceptance criteria to obtain a pass.

Evidence belongs outside the checkout or in ignored `.artifacts/`. A passing runner result proves only its selected checks; it does not authorize task closure, merging, or deployment. Keep the README explicit about implemented capabilities and future integrations.
