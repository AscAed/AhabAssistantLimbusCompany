# Reference Code Analysis Implementation Plan

> Archived on 2026-11-12 and superseded by `docs/references/aalc.md` and `docs/references/lalc.md`. Unchecked items below are historical planning state, not open work.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Produce evidence-backed reports on the exact local AALC and LALC checkouts, identifying reusable engineering practices, risks, and adaptation costs for the maintenance fork.

**Architecture:** Keep the two source analyses separate and add a concise comparative synthesis. Ground claims in checked-out code, tests, workflows, and build files; record repository identity with every report.

**Tech Stack:** Git, Python, Flutter/Dart source inspection, Markdown.

**Spec:** `docs/superpowers/specs/2026-11-12-project-modernization-design.md`

## Global Constraints

- Analyze local AALC commit `2fcb1b4620108c9bb0cf138f82790dd13f46356c` and LALC commit `431b432e22f0b0da08b95d7c478fa213be20b3e8`.
- Keep reference checkouts read-only; do not run network operations or tests in them.
- Do not recommend detection evasion, behavioral disguise, packet/process/memory bypass, or weakening security controls.
- Treat findings as applicable only to the recorded checkout identity.

## Review Focus

- Backend actions that contain unbounded polling or sleeps: document exact conditions and stop behavior.
- Cancellation during synchronous task execution: trace whether active work can reach a safe stop.
- Update flows that delete or replace target directories: document the exact path validation and rollback behavior.
- Workflow and command payloads with implicit schemas: identify validation boundaries and malformed-input handling.
- Test and CI coverage: distinguish automated tests from manually callable helpers and workflow configuration.

---

### Task 1: Freeze Reference Identities

**Files:**
- Create: `docs/references/aalc.md`
- Create: `docs/references/lalc.md`

**Interfaces:**
- Consumes: the already completed read-only AALC/LALC agent reviews, local reference repositories, and their Git metadata.
- Produces: each report starts with branch, HEAD, tags, clean/dirty state, and analysis limits.

- [ ] **Step 1: Prepare the report directory and reconfirm checkout identity**

Create `docs/references` only if it does not already exist.

Run `git -C "E:\PUBLIC\Project\AALC\Source Code\AhabAssistantLimbusCompany" status --short --branch`, `git -C "E:\PUBLIC\Project\AALC\Source Code\AhabAssistantLimbusCompany" rev-parse HEAD`, and `git -C "E:\PUBLIC\Project\AALC\Source Code\AhabAssistantLimbusCompany" tag --points-at HEAD`.

Run the same commands with `-C "E:\PUBLIC\Project\AALC\Source Code\LixAssistantLimbusCompany"`.

Expected: clean checkouts at the SHAs listed in Global Constraints, or stop and update the report scope to the observed identity.

- [ ] **Step 2: Inventory implementation and evidence**

Use the completed read-only reviews as the first-pass analysis. Map their evidence against UI/config, input, recognition/OCR, task flow, resource handling, tests, CI, and build/update coverage; inspect the local source only to verify load-bearing citations or fill documented gaps. Do not repeat already-supported exploration.

- [ ] **Step 3: Write the AALC report**

Record architecture, config/schema behavior, automation/input and screenshot boundaries, Mirror flow, resource/update path, tests/CI/build, reusable patterns, risks, and evidence limits in `docs/references/aalc.md`.

Every material claim must include a repository-relative path and line anchor. Separate confirmed code behavior from risk hypotheses.

- [ ] **Step 4: Write the LALC report**

Record frontend/backend boundaries, WebSocket commands and lifecycle, task graph/action registry, recognition interfaces, update/packaging path, tests/CI, reusable patterns, risks, and evidence limits in `docs/references/lalc.md`.

Every material claim must include a repository-relative path and line anchor. Separate confirmed code behavior from risk hypotheses.

- [ ] **Step 5: Review report coverage**

Check both reports against the five Review Focus entries and confirm their repository identities and paths still exist.

Expected: each report states what it did not inspect or execute; no claim implies current runtime or release verification.

### Task 2: Compare Transferable Practices

**Files:**
- Modify: `docs/references/aalc.md`
- Modify: `docs/references/lalc.md`

**Interfaces:**
- Consumes: the two independently grounded reports from Task 1.
- Produces: a short comparison section in each report covering adoption value, required adaptation, tests needed, and reject criteria.

- [ ] **Step 1: Compare only equivalent responsibilities**

Compare workflow, task cancellation, recognition abstraction, configuration validation, resource integrity, UI/backend communication, update safety, and repeatable tests where both projects expose equivalent behavior.

- [ ] **Step 2: Classify each recommendation**

Mark each item as reusable, reusable after adaptation, or avoid. Explain its fit to this fork's Python/PySide6 architecture and Windows input constraints.

- [ ] **Step 3: Verify citations and safety boundary**

Confirm each recommendation has source paths and does not advocate any prohibited behavior in Global Constraints.

Expected: `git diff --check` reports no whitespace errors; source paths resolve in the corresponding local checkout.
