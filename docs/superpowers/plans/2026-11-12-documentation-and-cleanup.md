# Documentation and Cleanup Implementation Plan

> Archived on 2026-11-12 and superseded by `docs/INDEX.md`, `docs/AGENT_WORKFLOW.md`, and `docs/audits/2026-11-12-self-audit.md`. Unchecked items below are historical planning state, not open work.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a concise AI-readable documentation system and remove or archive only content proven obsolete by current repository evidence.

**Architecture:** Keep one current fact source and link to it from focused documents. Preserve useful historical evidence with a visible date and validity boundary. Treat cleanup as an auditable inventory, not a directory-wide deletion.

**Tech Stack:** Markdown, Git, repository search, Python project documentation.

**Spec:** `docs/superpowers/specs/2026-11-12-project-modernization-design.md`

## Global Constraints

- Keep the repository instruction entry as `AGENTS.md`; do not add a duplicate `Agent.md`.
- Preserve historical findings, test results, and decision context when they still explain current code or past failures.
- Do not commit `config.yaml`, logs, personal settings, credentials, caches, or generated runtime artifacts.
- Do not remove code, assets, workflows, dependencies, or docs without reference, entry-point, packaging, and test impact evidence.
- Keep the project's security boundary explicit and consistent in all authoritative instructions.

## Review Focus

- A documented status must have one owner and a date/commit attached.
- Existing claims must distinguish current implementation from historical incidents.
- Internal links to moved Markdown and source-code anchors must continue to resolve.
- A cleanup candidate must have no live caller or be replaced with test-protected behavior.
- External content and logs must not be copied with secrets, local paths, or personal runtime data.

---

### Task 1: Establish the Documentation Map

**Files:**
- Create: `docs/INDEX.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: current root instructions, all tracked Markdown, and the approved design.
- Produces: one navigation entry and a concise agent initialization workflow.

- [ ] **Step 1: Inventory Markdown files and inbound links**

Run `git ls-files "*.md"` and search source/docs for links to `PROJECT.md`, `project_analysis.md`, `CODE_HEALTH_AUDIT.md`, `OPERATION_MODE_REFACTOR_AUDIT.md`, `BACKGROUND_INPUT_FIX.md`, and `CHANGES_SUMMARY.md`.

- [ ] **Step 2: Create documentation directories**

Create only the planned `docs/references`, `docs/audits`, `docs/architecture`, `docs/development`, and `docs/history` directories after confirming they do not already exist.

- [ ] **Step 3: Define source-of-truth precedence in `docs/INDEX.md`**

List the owner for current project status, architecture, development/validation commands, reference analysis, audit findings, and historical records. Link every listed document with a relative path.

- [ ] **Step 4: Refine `AGENTS.md`**

Retain project-specific rules and initialization requirements; link to `docs/INDEX.md` for detailed facts. Keep the Windows/Python 3.12 contract, user-work preservation, privacy, and security boundaries.

- [ ] **Step 5: Check the navigation**

Resolve each relative Markdown link from its containing file and check for duplicate authoritative status claims.

Expected: no broken internal link or conflicting source-of-truth statement.

### Task 2: Write Current Project and Development Facts

**Files:**
- Create: `docs/PROJECT.md`
- Create: `docs/architecture/overview.md`
- Create: `docs/development/environment-and-validation.md`
- Modify: `PROJECT.md`
- Modify: `assets/doc/zh/develop_guide.md`
- Modify: `assets/doc/zh/build_guide.md`

**Interfaces:**
- Consumes: current source, `pyproject.toml`, `uv.lock`, workflows, `main.spec`, build scripts, and the completed self-audit.
- Produces: current supported environment, module responsibility map, runtime boundaries, and reproducible local commands.

- [ ] **Step 1: Record verified product and platform facts**

Write project purpose, Windows support, Python version floor, dependency manager, supported operation modes, simulator boundary, runtime-data policy, and known limitations in `docs/PROJECT.md`.

- [ ] **Step 2: Map current code ownership and runtime flow**

Write entry-to-UI/config-to-automation/task-to-stop/update/resource boundaries in `docs/architecture/overview.md`; cite concrete source paths.

- [ ] **Step 3: Consolidate environment, testing, lint, and build instructions**

Document commands that were exercised during this goal, with their exact environment and results. Mark unexecuted commands as instructions, not verification evidence.

- [ ] **Step 4: Replace duplicated root summaries with links**

Reduce `PROJECT.md` to an entry/summary pointing to current docs. Update developer/build guides only where the repository's verified workflow differs.

### Task 3: Reconcile Historical Documents

**Files:**
- Modify or move, only after inbound-link review: `project_analysis.md`
- Modify or move, only after inbound-link review: `CODE_HEALTH_AUDIT.md`
- Modify or move, only after inbound-link review: `OPERATION_MODE_REFACTOR_AUDIT.md`
- Modify or move, only after inbound-link review: `docs/BACKGROUND_INPUT_FIX.md`
- Modify or move, only after inbound-link review: `docs/CHANGES_SUMMARY.md`

**Interfaces:**
- Consumes: current source audit, dated logs, verified tests, and Markdown inbound-link inventory.
- Produces: preserved historical evidence with current validity markers and no stale statements presented as current.

- [ ] **Step 1: Mark superseded or historical claims**

For each document, label the date/revision and identify claims superseded by current code or later test evidence.

- [ ] **Step 2: Preserve unique evidence and link to current facts**

Keep historical incident details, test records, and decisions needed to explain code history. Replace duplicated current status with links to the canonical files from Task 2.

- [ ] **Step 3: Move only documents with a clear historical destination**

Before each move, verify inbound links, update all references, and inspect the Git diff for accidental content changes.

- [ ] **Step 4: Verify internal links and safety language**

Search for outdated security-evasion recommendations and conflicting safety instructions. Expected: no current document advocates prohibited behavior.

### Task 4: Evaluate Cleanup Candidates

**Files:**
- Create: `docs/audits/cleanup-inventory-2026-11-12.md`
- Modify/delete: only candidates listed with evidence and verified by Task 2/3

**Interfaces:**
- Consumes: current code audit, `git ls-files`, entry points, import/ref searches, packaging declarations, tests, and Git history.
- Produces: itemized keep/archive/migrate/remove decisions with evidence and verification.

- [ ] **Step 1: Enumerate candidates**

Inspect tracked scripts, old modules, compatibility shims, duplicate assets, generated files, dependencies, workflows, docs, and ignored workspace directories such as `.pytest_cache`, `.ruff_cache`, `.tmp_pytest`, `test-run-temp`, `config_backup`, `logs`, `dist`, and `build`. Do not infer that a file is obsolete from age or name alone; do not read personal config contents or raw logs.

- [ ] **Step 2: Trace each candidate**

For code/content candidates, record imports, dynamic references, CLI entry points, CI/build inclusion, user configuration references, replacement behavior, tests, and history. For local directories, record exact path, type, size, last-write time, reparse/lock/process state, classification, and whether contents are mixed evidence or generated output.

- [ ] **Step 3: Apply only evidence-backed cleanup**

Remove or migrate an item only when all live references and required behavior are accounted for. For filesystem cleanup, verify each absolute target resolves inside the intended repository or named output directory before deleting it; preserve mixed or uncertain evidence and document the missing proof.

- [ ] **Step 4: Verify each changed candidate**

Run focused tests, import/search checks, and packaging/configuration checks relevant to the candidate; record exact outcomes, hashes where useful, and any errors in the inventory.
