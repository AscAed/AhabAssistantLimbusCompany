# Final Verification and Integration Implementation Plan

> Archived on 2026-11-12. Final validation results and integration status are recorded in `docs/audits/2026-11-12-self-audit.md`; unchecked items below are historical planning state, not open work.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Verify the complete maintenance batch against its stated scope, then create a focused, reviewable local commit and use a PR only if remote integration is warranted.

**Architecture:** Validate from narrow regressions through repository-wide checks, inspect packaging and docs separately, then audit the final diff and sensitive-file boundary before committing. Use native implementation in the current checkout because existing user changes overlap the repair paths; reserve separate agents for read-only analysis or final review.

**Tech Stack:** Python 3.12, pytest, Ruff, PyInstaller, Git, GitHub CLI if a PR is needed.

**Spec:** `docs/superpowers/specs/2026-11-12-project-modernization-design.md`

## Global Constraints

- The current repository declares Python `>=3.12`; local verification uses the observed `.venv` Python `3.12.13`.
- Preserve and review all pre-existing user modifications; do not use destructive reset/checkout commands.
- Do not include personal config, credentials, raw logs, local caches, or generated runtime data.
- Do not claim live-game or deployment identity verification unless directly established.
- Any external GitHub operation must inject the configured local proxy in that same terminal invocation.
- Do not push, merge, or auto-merge unless the verified repository state and required checks show it is necessary for the requested outcome.

## Review Focus

- The test suite must collect the actual tests that exercise changed contracts.
- Ruff and compile checks must include all changed Python files and their owning packages.
- PyInstaller output must be attributable to the verified source revision and version.
- Documentation links and source anchors must resolve after file moves.
- Final Git status must not hide ignored user data or include generated artifacts.

---

### Task 1: Run Focused and Full Validation

**Files:**
- Test: all focused modules recorded by the audit
- Test: full repository suite

**Interfaces:**
- Consumes: completed source fixes, docs, and cleanup inventory.
- Produces: dated validation record in `docs/audits/2026-11-12-self-audit.md`.

- [ ] **Step 1: Run each focused regression suite**

Synchronize code into the verified disposable validation copy, then run the exact pytest node or file there for lease restoration, screen visibility restoration, team selection, EGO gift selection, shop fusion, OCR failure handling, and every other fixed finding. Keep `config.yaml` and `config_backup` excluded from the copy.

Expected: each fix's new test and adjacent contract tests pass.

- [ ] **Step 2: Run Python syntax and collection checks**

From the disposable validation copy, run the original local interpreter with an isolated bytecode prefix: `E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany\.venv\Scripts\python.exe -X pycache_prefix=.tmp_pycache_codex_final -m compileall -q app module tasks utils scripts main.py main_dev.py updater.py`.

From the disposable validation copy, run `E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany\.venv\Scripts\python.exe -m pytest --collect-only -q -p no:cacheprovider`.

Expected: zero syntax errors and zero collection/import errors.

- [ ] **Step 3: Run the complete suite and Ruff**

From the disposable validation copy, confirm `.tmp_pytest_codex_2026_11_12_final1` does not exist, then run `E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany\.venv\Scripts\python.exe -m pytest -ra -p no:cacheprovider --basetemp=.tmp_pytest_codex_2026_11_12_final1`. Increment the suffix for later runs and never reuse an existing basetemp path. Remove only test/bytecode directories created inside the disposable copy after confirming their exact paths.

Run `.\.venv\Scripts\ruff.exe check app module tasks utils scripts tests main.py main_dev.py updater.py`.

Expected: pytest passes and Ruff exits successfully; report exact counts and warnings.

### Task 2: Verify Packaging and Documentation

**Files:**
- Modify: `docs/audits/2026-11-12-self-audit.md`
- Build outputs: local `dist/` only

**Interfaces:**
- Consumes: exact source revision, build script, `main.spec`, and canonical version configuration.
- Produces: package build result and verified documentation link report.

- [ ] **Step 1: Inspect build script side effects**

Review `scripts/build.py`, `main.spec`, version injection, archive commands, and output cleanup before running packaging. The current script recursively removes `./dist` at startup.

- [ ] **Step 2: Build using the repository's declared version**

Run `.\.venv\Scripts\python.exe scripts\build.py --version 1.0.9` only after confirming `dist/` is absent. If it exists, preserve it and record the build as unrun until an isolated output path is available.

Verify `dist\AALC\AALC.exe` and `dist\AALC_1.0.9.7z` exist, then inspect the archive with `7z l`. The build script does not check every subprocess result, so output existence and archive listing are required evidence. Generated outputs stay outside the commit.

- [ ] **Step 3: Check documentation navigation**

Resolve Markdown links from their source files, verify source anchors where used, and check that all canonical docs appear in `docs/INDEX.md`.

### Task 3: Audit and Commit the Final Diff

**Files:**
- Modify: all files changed by the approved plan

**Interfaces:**
- Consumes: validated code/docs changes and current status.
- Produces: one or more logical commits on a `codex/` branch and a clean post-commit worktree.

- [ ] **Step 1: Review the complete diff**

Run `git diff --check`, `git status --short --untracked-files=all`, and inspect staged/unstaged changes, new files, deleted files, and ignored paths that could affect validation.

Expected: no unexplained changes, personal data, runtime logs, or build/test artifacts.

- [ ] **Step 2: Confirm branch and commit scope**

Create `codex/project-maintenance-2026-11-12` only after verifying the current worktree and that the branch name is unused; preserve all existing user changes. If the name already exists, choose another `codex/` name. Group commits by coherent functional/documentation responsibility.

- [ ] **Step 3: Commit verified work**

Use concise action-oriented subjects. Do not commit failed or unverified changes.

- [ ] **Step 4: Verify post-commit state**

Run `git status --short --branch`, record commit IDs, and confirm the worktree is clean.

- [ ] **Step 5: Decide whether a PR is needed**

Inspect remote tracking and required checks. If a PR is warranted, prepare it from the verified branch using the configured proxy. Consider auto-merge only when the repository's required checks and permissions permit it and the exact PR head is verified.
