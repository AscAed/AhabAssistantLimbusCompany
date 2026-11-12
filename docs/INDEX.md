# Documentation Index

This index is the entry point for maintainers and coding agents. Current facts belong in one document; dated audits and historical notes are evidence, not live status.

## Current Sources

| Topic | Source |
| --- | --- |
| Agent initialization, change boundaries, and safe verification | [Agent workflow](AGENT_WORKFLOW.md) |
| Product scope, platform, dependency contract, and current limitations | [Project facts](PROJECT.md) |
| Runtime ownership and major control/data paths | [Architecture overview](architecture/overview.md) |
| Local environment, tests, lint, build, and network commands | [Development and validation](development/environment-and-validation.md) |
| Current audit findings, repairs, and validation evidence | [2026-11-12 self-audit](audits/2026-11-12-self-audit.md) |
| Cleanup candidates and decisions | [2026-11-12 cleanup inventory](audits/cleanup-inventory-2026-11-12.md) |
| Exact local AALC and LALC reference checkouts | [AALC](references/aalc.md), [LALC](references/lalc.md) |

## Evidence Rules

- Source code, tests, lockfiles, CI workflows, and commands run against the named checkout establish current facts.
- A report must name its date and source revision. Do not reuse a historic test count as a current result.
- A process, package, or release is verified only when its identity is directly connected to the current source revision.
- A static risk is not a reproduced incident. Label hypotheses and unresolved runtime conditions.
- Reference-project findings apply only to the checkout SHA recorded in that report.

## Historical Records

Historical audits and implementation notes are listed in the [history index](history/README.md). They explain prior decisions and incidents; use the current audit and project facts for today's state.

The repository's root `AGENTS.md` is ignored by `.gitignore` and is local guidance. The tracked, shareable workflow is [AGENT_WORKFLOW.md](AGENT_WORKFLOW.md).
