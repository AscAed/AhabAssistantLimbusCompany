# Documentation Investigation Baseline

Date: 2026-11-12. Checkout examined: `dc7339fb02907d96d56230621fedc896e0e2fa00`, branch `codex/project-maintenance-2026-11-12`. This is a dated, read-only investigation, not a runtime qualification. Current product facts remain in [Project Facts](../PROJECT.md); prior test and build evidence remains in the [self-audit](2026-11-12-self-audit.md).

## Scope and Evidence

| Area | Observed evidence and limit |
| --- | --- |
| Workspace | `git status --short --branch --untracked-files=all` listed no changed paths; enumeration of `.pytest_cache/`, `.tmp_pytest/`, and `test-run-temp/` was denied. This is not proof of their contents. They were retained. |
| Startup | `main.py` selects the executable/source directory, initializes logging, requests elevation, creates the Qt application and uses a localhost socket for instance arguments. The source alone does not establish behavior on every Windows configuration. |
| Configuration | `module/config/config.py:397-406,573-620` writes the destination directly and has a daemon writer. The shutdown barrier and interruption durability remain unproven; no configuration-loss incident was reproduced. Personal configuration was not read. |
| Capture and recognition | `module/automation/screenshot.py` selects Windows or simulator capture; `module/automation/automation.py:352-428` has bounded failure/restart behavior and cooperative checks around capture. `module/ocr/ocr.py` distinguishes engine failure from a valid empty result. Native calls already blocked inside the OS cannot be assumed interruptible. |
| Tasks | `tasks/base/task_engine.py`, `tasks/base/script_task_scheme.py`, `tasks/mirror/`, and `tasks/teams/` implement task dispatch and game-specific workflows. Tests use mocks and fixtures; their presence is not live-game evidence. |
| Updates | `module/resource_sync/manifest.py` validates relative paths and `service.py` checks contained paths, package hash and pre-copy file hashes. `updater.py` also checks incremental paths. Transactional recovery, actual remote content and packaged update behavior remain unqualified. |
| Build | Python `>=3.12` is declared; CI selects 3.12 and installs from `uv.lock`. `scripts/build.py` deletes `dist/`, builds app and updater, copies assets and archives them. The dated self-audit describes an isolated successful build and its limitations; this investigation did not rebuild or launch it. |
| Deployment | A process-name query for AALC/Ahab returned no match. This does not identify installed packages, executables with other names, remote releases, or an active game/simulator. No deployment identity or live operation was verified. |
| Logs | `logs/debugLog.log` last modified 2026-08-20, 1,399,802 bytes; a local pattern count found a traceback. The historical rules record an OpenCV template-size assertion and subsequent recognition failures. Neither establishes a current reproducible root cause; raw log contents and personal settings are not reproduced here. |
| References | Local AALC `2fcb1b4620108c9bb0cf138f82790dd13f46356c` and LALC `431b432e22f0b0da08b95d7c478fa213be20b3e8` are read-only static references. See their [AALC](../references/aalc.md) and [LALC](../references/lalc.md) reports for evidence and unresolved questions. No reference tests or deployments were run here. |

## Follow-up From the Referenced Chat

- **Team failure propagation, observed in source and tests:** daily EXP/thread paths return `False` when `select_battle_team` fails; Mirror raises on initial formation failure and bounds its team-selection attempts. `tests/unit/tasks/base/test_team_selection_propagation.py` contains mock-based cases for these paths. This resolves the specific concern that those examined callers unconditionally ignore failure; it does not establish all callers or real-game behavior. No tests were executed during this documentation investigation.
- **Production stop propagation, partially observed:** `ProductionWork.run()` installs a thread-local callback and screenshot operations consult it. The production loop still has `msleep` calls, an unbounded image-wait loop, and calls into `make_enkephalin_module`, whose own loops and sleeps require path-by-path stop and timeout review. A stop request is not proof of a bounded stop latency. Existing OCR tests do not establish cancellation through all these paths.

## Evidence Gaps and Lessons

- The 2026-11-12 isolated full-suite and build results are historical snapshots; they are neither a fresh run against this documentation change nor proof of a launched or installed executable. Preserve their source and exact scope.
- RapidOCR's declared `opencv-python` metadata and the locked headless OpenCV installation need a separate dependency and packaging investigation; do not install both distributions as a casual fix.
- A visible-window input lease is the current documented production path; alpha-zero hit targeting and native failure recovery need isolated Windows evidence. A mock cannot prove native delivery.
- Importing configuration can create local state. Use a configuration-free disposable copy for future tests, protect existing `dist/` before building, and preserve inaccessible scratch/cache data. See [development and validation](../development/environment-and-validation.md) and the [cleanup inventory](cleanup-inventory-2026-11-12.md).
- Shop fusion, EGO selection, route performance and cancellation latency need reproducible fixtures and measurements before their causes, severity or improvement are asserted.

For proposed changes and explicit validation gates, see [target architecture and optimization](../architecture/target-and-optimization.md) and the [implementation roadmap](../development/implementation-roadmap.md).
