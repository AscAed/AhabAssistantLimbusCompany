# Current Fork Self-Audit

Audit date: 2026-11-12. This audit records source, offline test, lint, and local build evidence. It does not qualify live-game behavior or a deployed release.

## Scope and Identity

- Checkout: `E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany`.
- Branch at audit start: `codex/project-maintenance-2026-11-12`, based on `fe50f94d8b55e953f73f6f3eb0bd2baceb770ead`.
- Local reference AALC: clean checkout `2fcb1b4620108c9bb0cf138f82790dd13f46356c`; local LALC: clean checkout `431b432e22f0b0da08b95d7c478fa213be20b3e8`. Their conclusions apply only to those SHAs; see [AALC](../references/aalc.md) and [LALC](../references/lalc.md).
- The starting worktree had eight modified tracked source/test files, two untracked regression-test files, and untracked analysis/planning documents from the prior task. Those changes were reviewed and carried forward; the temporary bytecode file was excluded.
- Root `AGENTS.md` is ignored by `.gitignore`, so it remains local. The tracked agent workflow is [docs/AGENT_WORKFLOW.md](../AGENT_WORKFLOW.md).

Evidence labels in this report: **Observed** means a command or source inspection from this checkout; **Historical** means earlier reports or logs; **Open** means a confirmed limitation or a hypothesis without a reproducer.

## Runtime and Artifact State

- **Observed:** `.venv` uses Python `3.12.13`; Ruff is `0.13.1`; uv is `0.11.28`.
- **Observed:** the final process query found no running `AALC` process. Its executable identity and any installed release therefore remain unverified.
- **Observed:** the source checkout has no `dist/` or `build/` directory. `logs/debugLog.log` was last modified `2026-08-20` and is historical evidence.
- **Observed:** a prior scratch copy ending in `_run1` contained a `config.yaml`; its contents were not read or changed and the copy was not used. Two new scratch copies were created with configuration exclusions; pytest later created local configuration/backup state and the final build wrote artifacts there. Those generated configs were not read or copied to the source checkout.
- **Cleanup:** exact removal of `_run2` and `_run3` was blocked by access-denied pytest temp directories; the approval review rejected recursive deletion because the copies contain generated config/build/test data. Both remain outside the repository. No ACL changes or forced deletion were attempted.
- No live game, simulator device, remote update, or installed package was operated during this audit.

## Validation

The project loads `module.config` during import. Tests were run in a disposable source copy that excluded the source checkout's `config.yaml*`, `config_backup`, logs, caches, virtual environment, and ignored runtime data. Temporary directories were unique per test run.

| Check | Result |
| --- | --- |
| Python compile | `compileall` passed for `app module tasks utils scripts main.py main_dev.py updater.py` with a separate bytecode prefix. |
| Focused regressions | 193 passed, 2 skipped across 195 changed-area tests. Both skips require creating symbolic links, which this environment does not allow. |
| Pytest collection | 250 tests collected with no collection errors. |
| Full pytest | 248 passed, 2 skipped. Both skips require creating symbolic links, which this environment does not allow. |
| Ruff | `ruff check --no-cache app module tasks utils scripts tests main.py main_dev.py updater.py` passed. |
| Diff whitespace | `git diff --check` passed; Git reported only its existing LF-to-CRLF notices for touched files. |
| Dependency metadata | `uv pip check --offline` confirms `rapidocr==3.4.1` requires `opencv-python`, while `opencv-python-headless==4.11.0.86` is installed. This mismatch remains open; both OpenCV distributions were not installed together. |
| Windows build | `scripts/build.py --version 1.0.9` completed in the disposable copy. Main executable, updater executable, and archive were produced; the archive listing contains both executables and `assets/config/version.txt` with `1.0.9`. Archive SHA-256: `4E32EC69566447FA97DAF57D6E9B9FA11A4D3EB066E5F64A5E58CE2F3B50C572`. |

The ordinary sandbox denied pytest temporary-directory enumeration during an earlier baseline run. Running the same file-tool tests through the authorized test path passed all five tests; no ACLs were changed. The final full suite completed without that environment error.

The build ran with the repository's bundled `assets/binary/7za.exe` exposed as `7z.exe` only inside the scratch copy because the host had no `7z` command on `PATH`; the virtual environment's `Scripts` directory was also added to `PATH` for `pyside6-lrelease`. PyInstaller emitted a third-party invalid-escape warning, an ignored macOS `AppKit` import warning, and notices that optional RapidOCR v5 model files were absent. The archive passed 7-Zip integrity verification, and its version file contains `1.0.9`. The executable was not launched.

## Repairs

| Area | Change and regression evidence |
| --- | --- |
| Input coordinates and timing | Removed detection-evasion coordinate and interval variation from `Automation`; click actions retain detected coordinates and the configured capped interval. Simulator swipe points are deterministic and keep their endpoints. Covered by `tests/unit/module/automation/test_input_policy.py` and updated input contracts. |
| Focus lease and window visibility | Lease rollback now restores the original position and visibility when acquisition fails. Layered color key, alpha, and flags are retained; native restore failure is reported; a foreground-query exception no longer skips position or visibility restoration. Production leases now use a visible window because zero-alpha mouse hit testing is not native-qualified. |
| Screenshot and startup recovery | `take_screenshot()` accepts a cooperative stop callback, allows at most one foreground restart, and raises after persistent failure. `find_element()` no longer waits indefinitely for an inner screenshot. Game-window discovery has a 120-second deadline with stop checks; `Screen.set_win()` checks at most five times; tool-window creation has a 10-second deadline and cancels a queued start. |
| Team selection and formation | Screenshot capture is limited to three attempts, team clearing to 30 passes, and callers stop when clearing, capture, or team-anchor identification fails. Wheel/drag scrolling is accepted only after a change in the team-list pane; unchanged content is accepted at the top only when OCR places the first team row in the top band. An unverified scroll switches to one visible drag attempt and then stops. The missing-anchor regression failed with `None` before the fix and now returns `False`; the final focused team-formation file passed 9 tests. |
| OCR | `OCR.run()` now raises `OCRExecutionError` for conversion/engine errors while preserving a valid empty RapidOCR result. The enkephalin reader bounds capture attempts and propagates OCR errors; the production worker reports them through its error signal. |
| Resource and updater paths | Manifest paths reject non-string, absolute, drive-qualified, ADS, parent-traversal, and invalid Windows path components. Resource copy/delete paths and every incremental updater path are checked against their intended root before mutation. Sentinel tests verify outside files remain unchanged. |
| Task and window lifecycle | Manual stop signals the worker before cleanup. Startup checks the stop flag, and main/tool windows defer close until workers finish; user-facing worker termination calls were removed. Recovery failures are recorded on the task and logged without replacing the original task exception. |
| Mirror screenshot failures | Default and farthest-distance route selection stop when initial screenshot acquisition fails instead of looping on `None`. |
| Tool startup | The UI processes events while waiting for tool initialization, then cancels startup and returns after the deadline. |
| Documentation and lint | Added a canonical documentation index, agent workflow, project facts, architecture and validation guides, cleanup inventory, and exact-checkout reference reports. Historical reports were moved and labeled; task-planning drafts remain marked as superseded. Corrected the Python version and broken English documentation links; fixed baseline Ruff import findings. |

## Open Findings

- **Config persistence:** `_save_config()` writes directly to the target file, and the delayed writer is daemonized. `flush()` only writes when `_pending_save` is true and does not wait for a write already queued or in progress (`module/config/config.py:397-406,573-620`). No data-loss incident was reproduced. Atomic replacement and a tested shutdown barrier need a dedicated change because they affect user configuration durability.
- **Mirror selection:** EGO gift selection still uses level anchors with fixed grid offsets; current tests do not cover multiple layouts, scales, or post-scroll visibility. The claim that aggressive shop fusion is broken remains unproven; existing offline checks do not establish real-game success.
- **Native hit targeting:** the hidden-window alpha-zero helper remains as a low-level utility, but the production lease path does not select it. No isolated two-window Win32 test or live-game input test established that global `SendInput` targets the hidden game window; visible window movement during a lease is the current behavior.
- **Cooperative cancellation:** Python stop checks run between screenshot operations. A native screenshot/API call already blocked inside the operating system cannot be interrupted until it returns. `Screen.init_handle()` also contains an internal wait, so the 120-second outer window deadline may be observed only after that call returns.
- **Runtime qualification:** No real game, simulator, update server, or built executable was exercised. The scratch build is not evidence of deployment identity.
- **Dependencies:** Resolve the `rapidocr`/`opencv-python-headless` metadata mismatch only after verifying the impact on Qt and PyInstaller packaging.
- **Test environment:** Two symlink containment tests remain skipped because symlink creation is unavailable in this environment.
- **Deferred documentation minor:** `assets/doc/en/README_EN.md` repeats the project documentation index bullet. It has no runtime impact and is retained as a polish follow-up.

The itemized cleanup disposition is in [cleanup inventory](cleanup-inventory-2026-11-12.md). Historical audit drafts remain under [history](../history/README.md).

The later read-only [documentation investigation](2026-11-12-documentation-baseline.md) checks the committed `dc7339fb` baseline and records follow-up evidence for team failure propagation, production cancellation and deployment identity. Its findings do not retroactively extend the scope of the tests or build recorded above.
