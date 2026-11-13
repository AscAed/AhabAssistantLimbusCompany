# Initial Self-Audit Draft (Superseded)

This is the initial audit draft from the interrupted work session. Its status, findings, and validation table were superseded by the final dated audit in `docs/audits/2026-11-12-self-audit.md`; retain this file only as historical context.

Audit date: 2026-11-12

## Scope and Evidence Rules

- Target checkout: `E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany`, branch `codex/project-maintenance-2026-11-12`, base `fe50f94d8b55e953f73f6f3eb0bd2baceb770ead`.
- Source reviews: local AALC `2fcb1b4620108c9bb0cf138f82790dd13f46356c` and LALC `431b432e22f0b0da08b95d7c478fa213be20b3e8`; see [AALC analysis](../references/aalc.md) and [LALC analysis](../references/lalc.md).
- Evidence labels: **Observed** means direct current command/source output; **Historical** means old logs or reports; **Hypothesis** requires a reproducer; **Unverified** means a runtime or external artifact was not identified.
- The starting worktree contained 7 modified source/test files and the untracked `tests/unit/module/game_and_screen/test_screen.py`. These are preserved and treated as user changes.

## Runtime and Build Identity

- **Observed:** project local environment is Python `3.12.13`; Ruff is `0.13.1`.
- **Observed:** an `AALC` process was running, started `2026-11-12 01:19:50`; its executable path was not available through the process query.
- **Observed:** the checkout contains no `dist/` or `build/` directory.
- **Observed:** `logs/debugLog.log` was last modified `2026-08-20`; it is historical evidence, not a current-run log.
- **Unverified:** no build artifact has been tied to the running process, so deployed source and binary identity are unknown.
- **Data handling:** `config.yaml`, `config_backup/`, logs, virtual environments, caches, and generated runtime data were excluded from the test copy. The personal configuration contents are not reproduced here.

## Initial Validation

The project’s import-time configuration loader reads the relative `config.yaml` and attempts a timestamped backup under `config_backup/`. One initial pytest collection attempt in the source checkout imported `module.config` and therefore read/parsed the ignored user config into the test process before failing with `PermissionError` while opening a new backup file. No config contents were displayed or copied, and no backup file was written. This was an audit deviation from the intended privacy boundary; subsequent pytest runs use a disposable copy that excludes `config.yaml` and `config_backup/`.

| Check | Result | Evidence |
| --- | --- | --- |
| Python compile | Pass in disposable copy with a separate bytecode prefix. Default compile failed because the existing root `__pycache__` rejected bytecode writes. | `python -X pycache_prefix=... -m compileall -q app module tasks utils scripts main.py main_dev.py updater.py` |
| Pytest collection | 139 tests collected, no collection errors in disposable copy. | `python -m pytest --collect-only -q -p no:cacheprovider` |
| Full pytest baseline | 132 passed, 7 failed. All seven failures were in `WindowMoveInput` tests. | `python -m pytest -ra -p no:cacheprovider --basetemp=pytest-baseline-full1` |
| Ruff baseline | 2 findings: `I001` and unused `MagicMock` (`F401`) in `tests/test_batch_scroll_fix.py`. | `ruff check --no-cache app module tasks utils scripts tests main.py main_dev.py updater.py` |
| Installed dependency metadata | `uv pip check` reports `rapidocr 3.4.1` requires `opencv-python>=4.5.1.48`, while the environment installs `opencv-python-headless 4.11.0.86`. The lock explicitly overrides `opencv-python` under an impossible Python marker. | `pyproject.toml:27,33,55`, `uv.lock:11,3723-3737`, local `uv pip check` |

The OpenCV metadata mismatch is currently a declared headless-wheel substitution and `cv2` imports/tests run in this environment. It remains a packaging/interpreter consistency item to document or resolve; do not install both wheels without checking Qt/PyInstaller effects.

### Baseline Failure Triage

The 7 failing tests are:

- `test_window_move_input_rejects_driver`
- `test_window_move_scroll_uses_focus_lease_and_send_input`
- `test_window_move_scroll_reports_send_input_failure`
- `test_window_move_click_uses_send_input_without_cursor_motion`
- `test_window_move_drag_refreshes_hit_target_before_and_after_window_move`
- `test_window_move_click_restores_position_after_send_input_failure`
- `test_window_move_lease_restore_failure_is_reported`

**Confirmed test-fixture mismatch:** the current input changes recheck `GetLastInputInfo` after `_wait_for_user_idle()` at `module/automation/input_handlers/input.py:1197-1208`, while the affected tests only mock `_wait_for_user_idle()` and do not supply a valid post-wait elapsed time. `_lease_handler()` sets the new state to `"unknown"` but does not stub `_get_last_input_elapsed_ms()` in `tests/unit/module/automation/test_input_contract.py:180-188`. Running the seven nodes with a temporary 600 ms elapsed-time stub made all 7 pass; no source or test files were changed for that diagnostic. Update the test fixtures to model the new precondition, then retain the separate low-elapsed-time rejection test.

The ordinary sandbox run also hit `PermissionError` while pytest iterated its temporary directory during shutdown. Re-running the full suite in the config-free disposable copy with the permitted test process completed normally; its results are the 132 passed / 7 failed shown above. The `tmp_path` file utility cases passed in that run.

## Historical Claim Revalidation

- The old claim that `Automation` lacked `batch_mouse_scroll` is stale. Current `module/automation/automation.py:62-105` conditionally binds it, and the team selection path calls the public API.
- The old claim that ROI and match-location caching were absent is stale. Current `module/automation/automation.py:394-523` implements default ROI and location-cache behavior.
- The historical theme-pack reset failure is fixed in current code: `reset_to_default()` reads the example/default config via `theme_list.load_config()` at `app/theme_pack_setting_interface.py:1068-1083`.
- Operation-mode migration is now explicit and rejects unsupported values: `module/config/config.py:27-43,289-290`; `assets/config/config.example.yaml:19` declares the canonical mode.
- The fixed EGO grid-offset concern remains present and unproven against multiple layouts.
- The fusion failure claim is unproven; static inspection shows level checks in the candidate cells.
- August log entries establish historical screenshot/template failures and the earlier scroll-binding error, not the current root cause.
- `project_analysis.md:60-62` still recommends anti-detection randomization, and `ORIGINAL_REQUEST.md` describes that as a requirement; both conflict with the current root safety boundary. `CODE_HEALTH_AUDIT.md:385-388,530-531` later says the input was determinized, but current `automation.py` still contains explicit random offset/interval code.

## Deep Audit Findings

These findings are based on the current checkout and current user diff. No production fixes have been applied yet.

| Priority | Finding | Evidence | Required disposition |
| --- | --- | --- | --- |
| High | `Automation` still randomizes click coordinates and action intervals with an explicit comment saying this is to evade uniform-click detection. | `module/automation/automation.py:234-240,279-290`; the random offset and interval were added in commit `c62cb3ae` (2026-07-13). This conflicts with the current `AGENTS.md` security boundary and earlier documentation that claimed input had been made deterministic. | Remove evasion-specific coordinate/timing randomization. Add deterministic contract tests before implementation. |
| High | A transparent lease can leave the window hidden if acquisition raises after hiding and before returning a lease. | Initially reproduced by `test_window_move_begin_lease_restores_state_when_position_set_raises_after_move` and `test_window_move_begin_lease_restores_visibility_when_activation_raises`. | **Fixed in current worktree:** acquisition captures the original rect and restores foreground, position, and visibility on false activation or exceptions. Both tests pass. |
| High | Simulator swipes still use random Bézier control points and sampling to vary gesture geometry. | `module/automation/input_handlers/simulator/__init__.py:4-52`; used by `module/automation/input_handlers/simulator/mumu_control.py:1015,1099,1155` and `pyminitouch/actions.py:302-314`. | Replace with deterministic geometry while preserving endpoint and minimum-distance contracts; add repeatability and endpoint tests. |
| High | Resource-sync manifest paths are not validated as contained relative paths before they are used to derive extraction and asset targets. | `ResourceFileEntry.from_dict()` coerces `path` to `str` but does not reject `..`/absolute paths (`module/resource_sync/manifest.py:26-63`). A no-write probe accepted `../outside.txt`; the service joins the value to `assets_dir` and `extract_dir`, then copies/unlinks (`module/resource_sync/service.py:703-730`). Archive member checks are separate (`utils/archive_7z.py:150-173`). There is no `tests/unit/module/resource_sync/` suite. | Add offline traversal/absolute-path tests and enforce containment for both extracted source and asset target before any copy or deletion. |
| High | Incremental updater manifest paths preserve `..` and are joined to the installation root before delete/copy operations. | `_normalize_manifest_path()` removes only empty and `.` parts (`updater.py:193-206`); a no-write probe returned `..\outside.txt`. `_apply_incremental_update()` uses the result in `rmtree`, `remove`, and `copy2` paths (`updater.py:135-189`). Archive-member validation does not validate the contents of `changes.json`; existing updater tests cover retry bounds but not path containment. | Reject absolute, drive-qualified, and parent-traversal paths; prove delete/copy targets remain under the installation root with temporary-directory tests. |
| High | Manual simulator stop can enter an unbounded reconnect loop before it sets the task stop flag; UI reset follows a fixed 2-second wait even if the worker remains alive. | `app/farming_interface.py:611-657` retries `clean_connect()` with a bare `except` and no wait/stop check before calling `stop_script()`; `stop_script()` sets `is_stop` and waits 2 seconds but returns if the worker is still active (`:733-740`). | Move stop signaling before simulator cleanup; use bounded reconnect attempts and preserve a stopping UI state until the worker actually finishes. |
| High | Closing the main window force-terminates the active task thread; closing tool windows can also terminate their workers after short waits. This bypasses cooperative cleanup. | Main task: `app/my_app.py:462-486`, with the worker passed into `TaskEngine` and screenshot hook restored in `finally` (`tasks/base/script_task_scheme.py:370-390,492-510`, `tasks/base/task_engine.py:99-160`). Tool windows: `tasks/tools/infinite_battle.py:192-205,234-242`; `tasks/tools/production_module.py:290-302,346-354`. | Route close through cooperative stop and defer window close until worker completion; remove forced termination from user-facing close paths. |
| High | A task stop request is not observed during initial game-window discovery; the task engine stop hook is installed only after `init_game()` returns. | `script_task()` calls `init_game()` before creating `TaskEngine` (`tasks/base/script_task_scheme.py:341-378`); `init_game()` loops on `screen.init_handle()` and sleeps 10 seconds with no stop check or attempt limit (`:124-182`). | Pass the task stop state into initialization or use a bounded initialization wait; test stop while the game window is absent. |
| Medium | Window visibility snapshot loses nonzero color keys and restore treats any layered window as click-through. | Initially reproduced by `test_hide_for_background_input_refuses_unreadable_layered_state`, `test_restore_background_input_visibility_reports_native_api_failure`, and `test_snapshot_and_restore_preserve_layered_color_key`. | **Fixed in current worktree:** the snapshot preserves color key/alpha/flags, unknown layered attributes refuse hiding, native false returns remain failures, and `isTransparent` follows `WS_EX_TRANSPARENT`. Focused screen tests pass. |
| High | A reset attempt can spin without delay when window metrics or a repeated `_set_win()` attempt raises. | `module/game_and_screen/screen.py:511-549`; the exception handler logs and immediately loops. `Screen.set_win()` is called from task initialization (`tasks/base/script_task_scheme.py:179-182`) and tools. | Add a bounded retry/deadline or propagate the failure after one recovery attempt; test a persistent Win32 sizing error. |
| Medium | The task engine silently discards errors from failure recovery before re-raising the original task exception. | `tasks/base/task_engine.py:147-158` catches all recovery exceptions and uses `pass`. | Preserve the original task error and report recovery failure separately; add a paired-error test. |
| Medium | `OCR.run()` maps all image, conversion, engine, and OCR errors to an empty `RapidOCROutput`, so callers cannot distinguish “no text” from an OCR failure. | `module/ocr/ocr.py:30-68`. | Add a typed failure/result distinction or a narrow exception contract and test malformed image, engine error, and genuine empty recognition separately. |
| Medium | Background-input verification still needs actual list movement; screenshot success or the static team marker is insufficient. | `tasks/teams/team_formation.py:88-93,177-215`; the initial dirty implementation has an unbounded screenshot loop and can set the state from a static marker or any captured frame. | Keep the planned bounded capture and scroll-pane movement check with one visible-mode retry. |
| Medium | `auto.find_element(..., take_screenshot=True)` has an unbounded inner screenshot loop that bypasses its own `max_retries`. | `module/automation/automation.py:424-476`; the legend special case has a related wait at `:446`. `take_screenshot()` has per-call recovery logic, but the outer `while` has no local deadline or attempt cap. | Replace with a bounded screenshot acquisition result that can report timeout distinctly from “target not found”. |
| High | Foreground screenshot recovery can repeat 60-second restart cycles without a total restart limit, and the task stop hook is only checked before entering `Automation.take_screenshot()`. | `module/automation/automation.py:330-377`; task engine hook is at `tasks/base/task_engine.py:99-108`. | Add cooperative stop checks inside screenshot recovery and a maximum restart/deadline budget; test stop during repeated capture failure. |
| Medium | Window initialization retries errors in a tight loop without a delay or limit. | `module/game_and_screen/screen.py:511-549`; `set_win()` is called by startup and tool flows, and exceptions in the verification loop are caught before immediately retrying. | Add a finite retry/deadline with a surfaced initialization failure, then test a persistent window API error. |
| Medium | EGO selection is covered only for a Level III row 1/column 1 anchor at scale 1 plus a bleed fallback; other coordinates/scales and scroll transitions are not demonstrated. | Fixed offsets remain at `tasks/mirror/mirror.py:1034-1084`; assertions are in `tests/unit/module/automation/test_milestone4.py:88-145`. | Extend deterministic cases for row, column, level, scaling, and not-visible-after-scroll; retain explicit unverified visual limits. |
| Open | Fusion still uses grid offsets, but the current code checks the cropped cells for Level III and an existing test asserts exactly three Level III cells are selected. | `tasks/mirror/in_shop.py:447-519`; `tests/unit/module/automation/test_milestone4.py:43-83`. | Do not label the strategy broken without reproducing a wrong selection or failed completion. |
| Medium | `test_batch_scroll_fix.py` contains a lint failure and duplicates parts of production logic rather than exercising only public behavior. | Baseline Ruff output: `I001` and unused `MagicMock` (`F401`) at `tests/test_batch_scroll_fix.py:2-3`; the tests define local scroll/fallback functions. | Reconcile with current test coverage; retain or replace only after confirming the production path remains covered. |

### Input Randomization Scope

- **Confirmed policy conflict:** `module/automation/automation.py:234-240,279-290` explicitly randomizes click offsets/intervals to evade detection; remove this behavior under the repository security boundary.
- **High-confidence policy conflict:** `module/automation/input_handlers/simulator/__init__.py:4-52` randomizes Bézier swipe controls and sampling; it is used by `MumuControl` and pyminitouch (`mumu_control.py:1015,1099,1155`, `pyminitouch/actions.py:302-314`). The historical request asks for humanized input while current `AGENTS.md` prohibits behavioral impersonation/randomization to evade auditing. Replace with deterministic geometry while preserving endpoint and spacing contracts.
- **Not classified as evasion from current evidence:** `tasks/battle/battle.py:608-618` adds a small random offset to a center click to skip a narrator animation; its introducing commit describes that purpose. The behavior still lacks a deterministic test and can be considered separately for coordinate reliability.

## Repair Progress

- `tests/unit/module/automation/test_input.py` and `test_input_contract.py` now supply a deterministic post-wait idle value for existing lease tests; the two input files pass 57 tests in the isolated copy.
- The focused driver preflight now rejects a configured physical driver before window hiding or movement. `test_window_move_input_rejects_driver` passed after the early guard.
- `module/automation/input_handlers/input.py` now captures the original window position before acquisition and rolls back position, foreground, and visibility if position-setting or activation raises. `module/game_and_screen/screen.py` now preserves the layered color key and propagates native restore failure.
- Focused input and screen validation: 65 passed. Team-selection bounds/movement verification, full suite, broad path fixes, deterministic input cleanup, UI stop lifecycle, and remaining audit items are still pending.

### Shutdown and Retry Inventory

The task engine checks a worker stop flag at task boundaries and through a temporary `auto.take_screenshot` hook; its main task call passes the worker object: `tasks/base/script_task_scheme.py:370-390`, `tasks/base/task_engine.py:99-160`. `script_task()` calls `init_game()` first, so this hook is not active during initial window discovery. Manual stop in `start_and_stop_tasks()` resets the start button and settings before it calls `stop_script()`, whose 2-second wait can return while the worker is still active: `app/farming_interface.py:611-657,733-740`. In simulator mode, `clean_connect()` retries before `stop_script()` sets that flag. The main window close path calls `terminate()` on the task thread; tool windows' own close paths may terminate internal workers after 1-3 seconds. Those force-kill paths can bypass cleanup.

The simulator reconnect loop in `app/farming_interface.py:632-648` is a confirmed unbounded retry, and it runs before `stop_script()` sets the stop flag. Standalone tool windows also terminate QThreads after one-second waits or during close (`tasks/tools/infinite_battle.py:192-205,234-241`; `tasks/tools/production_module.py:290-302,346-354`).

### Loop and Stop Classification

| Class | Representative paths | Assessment |
| --- | --- | --- |
| UI-side retries without a stop/attempt bound | Simulator cleanup in `app/farming_interface.py:632-648`; window verification exception path in `module/game_and_screen/screen.py:536-549` | Confirmed high-risk stop/start or busy-retry paths; repair is in queue. |
| Capture wait/recovery loops | `module/automation/automation.py:330-377,446,475`; `tasks/teams/team_formation.py:35,65,89,225,246,368`; `tasks/mirror/search_road.py:148,223`; `tasks/base/make_enkephalin_module.py:54` | Capture methods may themselves retry/restart. The task hook checks stop only when `auto.take_screenshot()` is entered, not during its internal recovery loop. Bound per-call and outer waits separately. |
| Task loops with explicit counters/deadlines | `tasks/mirror/mirror.py:118-199,241-534,1236-1268`; `tasks/mirror/in_shop.py:135-164,476-578,587-646,1002-1054,1110-1153,1222-1323,1599-1628`; `tasks/daily/` | Many use loop counts, `retry()`, or task screenshot hooks. Keep the existing task semantics and add local bounds where a failed recognition can bypass the counter. |
| Retry/recovery loops | `tasks/base/retry.py:104-145,194-225`; `tasks/base/back_init_menu.py:17-40` | `kill_game()` and `retry()` have elapsed-time checks; `back_init_menu()` resets its loop count after restart, so repeated restarts have no overall cap but remain screenshot/stop-hook dependent. |
| Persistent service loop | `module/config/config.py:607-617` | The daemon writer waits on an event by design; confirm shutdown flush behavior separately rather than treating the loop as a defect. |
| Bounded local loops | `tasks/mirror/mirror.py:1222-1230`; data traversal and layout loops | Team selection fails after six tries; ordinary finite traversal loops are not issues. |

An AST inventory also found `app/tools_interface._tool_start()` waiting on `tool.initialized` without a timeout (`app/tools_interface.py:101-122`). The worker sets `None` on its handled initialization failures, so retain this as a lower-priority timeout candidate unless a path can leave the flag unset.

## Remaining Audit Work

- Task 3 static review is complete for the planned entry/config, input/screenshot/OCR, task/stop, resource/update, build/CI, test, and Mirror/shop/EGO boundaries. Findings above are the repair queue.
- Add focused TDD regressions for path-containment, stop-lifecycle, deterministic-input, and bounded-wait findings; update idle-state test fixtures for the new contract.
- Re-run focused and full pytest in the config-free test copy; keep the personal configuration and the original cache/backup directories untouched.
- Build verification, documentation link validation, cleanup inventory, and final disposition are pending.
