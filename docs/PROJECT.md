# Project Facts

## Identity

- Project: AhabAssistantLimbusCompany (AALC), a Windows desktop automation application for Limbus Company.
- This checkout is a maintenance fork. It is a stability and diagnostics project, not a general game AI or a proof of optimal play.
- Documentation assessment on 2026-11-14 inspected `main` at `d6c481df` (PR #128 merge). A complete tracked-tree diff from the previously tested `4fdb201` snapshot lists only four documentation files; this comparison does not rerun tests, establish environment equivalence, or identify an installed build. See the [current stage assessment](audits/2026-11-14-stage-assessment.md).
- **Current-main validation (2026-11-15):** `main` at `15601e8af6d4f1d5f73656d735b02121a7b1e433` was archived into a fresh config-free snapshot (archive SHA-256 `5A210CD6269A4C5FD903850076DDE9F624A198D3CDAC968C1E2A3DA0C92D1192`) and tested with the existing Python 3.12.13 environment: **425 passed, 2 skipped out of 427 in 64.30s**. Both skips require Windows symbolic-link creation. Full Ruff and `compileall` passed. The archive omitted `.Jules` and `.jules` only to avoid their case collision on Windows; it contained no `.git` or personal config. Pytest generated a config inside the disposable snapshot; it was not read or copied. Offline `uv pip check` still reports RapidOCR's `opencv-python` metadata requirement while the project intentionally retains its locked `opencv-python-headless` distribution and uv override. The source/test tree is the same tree used for the latest package and archive checks recorded in the [implementation handoff](audits/2026-11-14-implementation-handoff.md). Neither executable was launched; startup and deployment remain unverified. Startup tracing found external version, resource-manifest, and announcement requests, administrator elevation, and runtime-directory writes.
- Historical assessment on 2026-11-14 used `main` at `895c8bbe539a7f6ab30507bdc73093824d98453d`. PR #125 subsequently merged to `main` as `2f0075141e0b66f940b69381b240f21587ec020d`; this is a source identity, not an installed or deployed release identity.
- The reliability batch based on `2f007514` was validated from a config-free snapshot made from `git archive HEAD` plus 40 then-visible worktree overlays, each SHA-256 checked at snapshot creation. The intended batch contains 39 project files; an unrelated user note in `.Jules/palette.md` was excluded from the proposed commit. The full suite collected 374 tests: 372 passed and 2 Windows symlink tests skipped because symbolic-link creation was unavailable. Ruff passed. See the [2026-11-14 implementation handoff](audits/2026-11-14-implementation-handoff.md) for exact paths, commands, and evidence boundaries.
- Immediately after PR #126 merged on 2026-11-14, `main` was at merge commit `2920cd7fd624ee62599e11ad323c96ce41a43257`, from reviewed head `d6ca73c1474e57c7854102e1715f20e41dc19fcd`. The implementation/test snapshot at `4fdb201faca9f08afac4c54196e75e9880b52500` passed 373 tests with 2 Windows symlink skips and Ruff; the later review-evidence commit changed only roadmap documentation. This records the post-merge source/test identity, not an installed or deployed release identity.
- A disposable package build and 7-Zip/asset comparison were completed against an earlier `895c8bbe`-based snapshot, before PR #125. Those artifact hashes remain historical evidence and do not validate the `2f007514` source tree or the reliability batch. The package was not launched and does not identify an installed or deployed release. Updater tests use mocked processes or a controlled child and temporary roots; no real process or live 7-Zip process was exercised.
- Earlier base-only, nine-overlay, eleven-overlay, 13-overlay, 14-overlay and 398-test packages are historical. The current 15-path package is identified in the implementation handoff and was checked without launching it; startup elevation, network checks, writable paths, updater behavior and deployment identity remain unverified.
- Declared package version: `1.0.9` in `pyproject.toml`.

## Platform and Runtime

- Windows desktop application; Python requirement is `>=3.12`. CI selects Python 3.12.
- `uv` is the preferred environment and lockfile manager.
- User-facing operation modes are `foreground_mouse` and `background_window`. Simulator input is a separate ADB/MuMu transport.
- `background_window` currently uses a visible window focus lease that may briefly reposition the game window; the physical cursor is not moved. Hidden alpha-zero input is not selected without native hit-target evidence.
- Configuration examples live under `assets/config/`. Personal `config.yaml`, backup files, logs, and runtime data are local data and must not be committed.
- Updates and resource synchronization perform network and filesystem operations; see the audit and architecture pages before changing them.

## Module Ownership

- `app/`: PySide6 UI and worker lifecycle.
- `module/config/`: typed settings, migrations, and persistence.
- `module/automation/`: screenshot coordination, image/text lookup, and input dispatch.
- `module/game_and_screen/`: game-window identity, geometry, and Win32 visibility state.
- `module/ocr/` and `utils/image_utils.py`: OCR and image recognition helpers.
- `tasks/base/`: task scheduling, retries, stop state, and recovery.
- `tasks/mirror/`: Mirror dungeon state flow, route decisions, shop handling, and EGO choices.
- `tasks/teams/`: team selection and formation.
- `module/resource_sync/` and `module/update/`, `updater.py`: resource and application update flows.
- `scripts/`, `main.spec`, and `updater.spec`: maintenance and Windows packaging.

## Current Boundaries

- Do not infer current deployment or release identity from the source tree, old logs, or a passing unit test.
- Real-game input, simulator compatibility, native Win32 behavior, and packaged execution require separate runtime evidence.
- Historical claims about EGO coordinates and shop fusion are not treated as proven failures without a reproducible fixture or incident.
- The [implementation roadmap](development/implementation-roadmap.md) is the current stage and next-action source; the [2026-11-14 stage assessment](audits/2026-11-14-stage-assessment.md) records the initial documentation-only review, later implementation updates, decisions and evidence boundaries. The [implementation handoff](audits/2026-11-14-implementation-handoff.md) and [2026-11-13 assessment](audits/2026-11-13-stage-gap-assessment.md) retain detailed validation and deployment evidence.
- The [target design](architecture/target-and-optimization.md) describes proposals rather than implemented capabilities. Earlier audits record dated evidence for their own snapshots.
