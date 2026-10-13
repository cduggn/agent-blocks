---
name: task-worker
description: Execute a defined repository task from a task file or issue queue, tracking ownership and acceptance evidence. Use when asked to pick up a task or work through a bounded queue.
---

# Task worker

Use the task store named by the user or project. If no store exists, use the [task template](assets/task-template.md) for a single-worker pilot. Do not introduce a second status store.

## Pick up

Read project instructions and the task's outcome, scope, dependencies, acceptance criteria, and required verifier IDs. A task is ready only when its blocking dependencies are complete and its outcome is specific enough to verify.

Claim through the store's ownership mechanism before editing. With Beads, inspect installed command help, then query ready work, read the chosen task, and claim it atomically. Losing a claim means choosing other ready work. Local task files support only one active worker; record the owner and do not claim concurrency safety.

## Execute

Choose the smallest applicable workflow: investigate for a cited answer, reproduce then fix for a defect, implement against acceptance criteria for a feature. Existing project workflows take precedence. Read only the skills relevant to this task; this skill does not require poteto-mode or authorize delegation.

Keep the task's implementation scope and operational authorization. A task assignment does not independently authorize messages, deployment, or merging. For a queue, work within its supplied run budget and stop when no ready work remains or the budget is exhausted.

## Verify and hand off

Resolve required checks using the [verifier contract](references/verifiers.md). Map every acceptance criterion to evidence; a successful generic test suite alone does not establish unrelated application behavior. Missing or unavailable required checks leave the task blocked, with a precise next action.

For command verifiers, use the bundled [runner](scripts/verify.py) with the task's verification snapshot and project registry, following the invocation in the contract. Run it afresh after relevant edits. A zero exit status establishes only that its registered checks passed; inspect their coverage before accepting the task. Never use an earlier successful report to override a current failure.

Record the tested revision or dirty snapshot, check results, artifact locations, and unresolved limits in the authoritative task. Recheck affected evidence after subsequent edits. Enter review only after required proof passes; close only when acceptance and any project-required review are satisfied. A task may be complete without its changes being merged.

On interruption, save the current run/process identifiers, workspace, completed steps, and next action. On pickup, inspect actual process and repository state before retrying. A stale timestamp alone is not evidence that a worker stopped. Release or reassign ownership through the store only after reconciling the prior run.
