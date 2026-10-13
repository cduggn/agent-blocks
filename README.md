# Agent Blocks

A modular starter for task-driven coding agents: define the outcome, let a worker implement it, and require verifiable evidence.

- **Available:** a worker skill, task template, shared/project verifier registry, and executable verification runner.
- **Next:** a real application pilot, Beads integration, then automatic task pickup and recovery.
- **Status:** early foundation; no background worker or task service is configured.

## What to take from poteto-mode

Poteto-mode is a router: it selects a playbook, applies relevant principles, and invokes supporting skills and verification. Its entrypoint depends on other files and host capabilities, so copying just SKILL.md would leave dependencies behind. Keep the routing idea, incremental verification, and reusable project recipes. Add design panels and parallel execution only after the basic loop works. [Upstream source](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/SKILL.md).

## The five blocks

| Block | Responsibility | Starting point |
| --- | --- | --- |
| Project instructions | Repository commands, boundaries, conventions | [Repository instructions](AGENTS.md) |
| Task | Outcome, context, acceptance criteria, dependencies, owner | [Task template](skills/task-worker/assets/task-template.md) |
| Worker skill | Claim a task, choose the workflow, implement, collect proof | [task-worker](skills/task-worker/SKILL.md) |
| Verifier registry | Map required outcomes to repeatable checks | [Contract and runner instructions](skills/task-worker/references/verifiers.md) |
| Dispatcher | Start a worker for ready work; manage retries and recovery | Manual invocation first; unattended service later |

Task → claim → implement → verify → review → done. A failed check returns to implementation; unavailable proof leaves the task blocked. Completion is distinct from merging or deploying.

Keep reusable workflow skills here. Keep application commands, feature maps, and verifier registrations in the application repository. Start with the existing [pstack’s verifier generator](https://github.com/cursor/plugins/blob/main/pstack/skills/create-verification-skill/SKILL.md) and [verifier maintenance skill](https://github.com/cursor/plugins/blob/main/pstack/skills/maintain-verification-skill/SKILL.md) as optional upstream references when creating real application verifiers; they are not bundled dependencies.

## Run the first block

From this repository root, on macOS or Linux with Python 3.9 or later:

```bash
python3 skills/task-worker/scripts/verify.py \
  --project . \
  --task examples/task.json \
  --registry examples/registry.json \
  --output /tmp/agent-blocks-verification
```

The [pilot task](examples/task.json) requires both a reusable relative-link check and a project-specific verifier behavior suite, registered in [registry.json](examples/registry.json). The command writes a unique evidence directory and exits 0 for pass, 1 for a failed check, or 2 for blocked/invalid input. Tests exercise the CLI against a working and deliberately broken application, missing checks and executables, timeouts, changed sources, duplicate registrations, empty requirements, and a failed rerun after earlier success.

To work a task in an agent session, explicitly point it at [task-worker/SKILL.md](skills/task-worker/SKILL.md) and the task's authoritative record. The skill is staged here, not globally installed. The JSON input is a verification snapshot of that record; it is not another queue. The runner checks registered commands and fingerprints listed sources. The worker still assesses whether those checks actually cover acceptance criteria and any required review.

## What current engineering teams document

- OpenAI recommends durable repository guidance, focused skills, concrete completion criteria, and automating workflows after they are stable. [Official best practices](https://learn.chatgpt.com/guides/best-practices).
- Anthropic's application harness experiments separate implementation from evaluation and use observable behavior to give the implementation agent useful feedback. The evaluator also needs calibration; a second model is not automatically a reliable judge. [Engineering report](https://www.anthropic.com/engineering/harness-design-long-running-apps).
- Cursor reports that complete development environments and durable execution are central to cloud-agent reliability. Its production approach separates execution, machine state, and conversation state. [Engineering report](https://cursor.com/blog/cloud-agent-lessons).

My recommendation from these examples: invest first in clear tasks, reproducible environments, and trustworthy checks. These are published practices and experiments, not evidence of one universal workflow used by all top developers.

## Advanced options and follow-up references

These are upgrade paths to evaluate as the workflow and models improve, not features implemented in this starter.

| Option | What it adds | Follow up |
| --- | --- | --- |
| Autonomous task pickup | An issue board feeding agents in isolated workspaces, with reviewable proof | [OpenAI Symphony](https://github.com/openai/symphony) — engineering preview; [architecture specification](https://github.com/openai/symphony/blob/main/SPEC.md) |
| Durable execution | Recovery after crashes, bounded retries, and persistent run state | [Cursor cloud-agent engineering](https://cursor.com/blog/cloud-agent-lessons) — describes its use of Temporal |
| Independent verification | Separate builder and evaluator, with feedback from the actual application | [Anthropic harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps) |
| Workflow evaluations | Replay representative tasks to compare model/skill changes on correctness, cost, and human intervention | [Anthropic agent evaluations](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) |
| Replaceable models and simpler workflows | Preserve task and evidence contracts while replacing agents and retiring unnecessary orchestration | [Cursor's lessons on reducing harness logic](https://cursor.com/blog/cloud-agent-lessons) |

Recommended order: reliable application verifiers → task pickup → recovery → independent review and measured parallelism. Keep model selection outside task definitions. Use evaluation results to decide whether an extra agent or workflow step earns its cost.

Foundational references: [poteto-mode](https://github.com/cursor/plugins/blob/main/pstack/skills/poteto-mode/SKILL.md), [Beads](https://github.com/steveyegge/beads), and [OpenAI best practices](https://learn.chatgpt.com/guides/best-practices). References reviewed on 2026-10-13; upstream products and APIs may change.

## Task tooling

| Choice | Use it for | Tradeoff and recommendation |
| --- | --- | --- |
| Local task files | Learning the workflow with one active worker | Easiest to inspect; no atomic claims or unattended pickup. Use for the first pilot only. |
| Beads | Persistent agent tasks, dependencies, ready-work queries, atomic claims | Current upstream uses Dolt and supplies a CLI. Adds database/setup work. Recommended next step for this local workflow. [Source](https://github.com/steveyegge/beads). |
| Linear with Symphony | A board feeding autonomous implementation runs | Symphony demonstrates polling Linear, isolated execution, and proof of work. It is an engineering preview for trusted environments; choose this route if a team board is the desired interface. [Source](https://github.com/openai/symphony). |

Beads records work; it does not by itself launch your coding agent. The worker uses `bd ready`, `bd show <id>`, and `bd update <id> --claim`, then verifies before closing work. A dispatcher supplies the recurring pickup. Check the installed version's help before integrating; current upstream documents setup that can also edit agent instructions and hooks. Keep one authoritative task store rather than synchronizing task status manually across Markdown and Beads.

## Staged plan

1. **Understand the blocks:** inspect the skill and contracts in this directory. Walk one task from acceptance criteria to evidence. This starter provides the structure.
2. **Prove one project:** choose one real feature or bug; register an existing check and one user-visible behavior check. Run the verifier against both known-good and deliberately broken behavior in a disposable test environment. Required failure must prevent completion.
3. **Use Beads:** import the task fields, express dependencies, and prove that two competing claims produce one owner. Run one worker at a time initially. Test a blocked task and a resumed task before expanding.
4. **Automate pickup:** add a dispatcher with bounded concurrency, isolated workspaces, a run budget, process/run IDs, and recovery after interruption. Prove it does not launch duplicate work or close a failed task. Consider Symphony if choosing Linear.
5. **Expand from evidence:** add application verifiers as features arrive. Add independent review or parallel workers where measured results justify the cost. Compare escaped defects, user corrections, completion time, and usage on representative tasks.

The starter includes executable verification and a framework pilot. Applying it to another application, integrating Beads, and enabling unattended execution are the next rollout blocks. The local tests establish the runner's behavior; they do not establish the quality of arbitrary future verifiers or autonomous workers.
