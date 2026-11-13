# Current Fork Audit and Repairs Implementation Plan

> Archived on 2026-11-12 and superseded by `docs/audits/2026-11-12-self-audit.md`. Unchecked items below are historical planning state, not open work. Final test evidence and remaining issues belong to the current audit.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Audit the current maintenance fork against its running and build evidence, then repair confirmed reliability defects with focused offline regression coverage.

**Architecture:** Establish a dated baseline first, inspect each responsibility boundary from entry points through task completion, and keep confirmed defects separate from hypotheses. Fix high-impact issues in small, test-backed units.

**Tech Stack:** Python 3.12, pytest, Ruff, PySide6, Win32 API wrappers, local logs and Git.

**Spec:** `docs/superpowers/specs/2026-11-12-project-modernization-design.md`

## Global Constraints

- Preserve the existing 7 modified files and untracked `tests/unit/module/game_and_screen/test_screen.py`; inspect and incorporate them only after reviewing their complete diff.
- Use the repository's Python 3.12 contract and local virtual environment where available.
- Do not send input to, close, update, or otherwise disturb the running AALC process.
- Do not read or commit `config.yaml`, credentials, runtime data, or raw unsanitized logs.
- Run offline tests before considering any real-game interaction.
- Do not implement detection evasion, behavior disguise, packet tampering, process/memory bypass, or weakened security controls.

## Review Focus

- A hidden window must be restored if any call during focus-lease acquisition raises.
- Missing or failed native layered-window attributes must not silently change pre-existing visibility state.
- Screenshot capture failure must end in a bounded, explicit failure instead of blocking forever.
- Background input may be marked supported only after an observable expected state transition.
- EGO selection and shop fusion coordinate assumptions must be tested before their historical failure claims are treated as proven.

## Execution Order

1. Complete Task 1 baseline.
2. Complete Task 3 full current-fork audit and record findings before editing production code.
3. Complete Task 2 only after Task 3 classifies the existing background-input risks.
4. Complete Tasks 4 through 8 in order: stop lifecycle, path containment, deterministic input, bounded recovery, and OCR failure semantics.

---

### Task 1: Record Baseline and Run Existing Checks

**Files:**
- Create: `docs/audits/2026-11-12-self-audit.md`
- Test: existing test suite

**Interfaces:**
- Consumes: current branch, exact existing diff, local environment, available logs, and build artifacts.
- Produces: a dated baseline distinguishing current evidence, historical evidence, hypotheses, and unavailable evidence.

- [ ] **Step 1: Prepare the audit directory, validation copy, and repository baseline**

Create `docs/audits` only if it does not already exist. Record branch, HEAD, remote-tracking relationship, modified and untracked paths, Python version, local artifact directories, and the running process identity as observable. Do not copy configuration contents or unsanitized log lines.

The source test collection imports `module.config`, whose relative `./config.yaml` path triggers a backup write to `./config_backup`. Run tests in `E:\PUBLIC\Project\AALC\.codex_test_workspace_2026_11_12_run1`, a disposable sibling of the repository. Before copying, confirm the destination does not exist and resolves directly under `E:\PUBLIC\Project\AALC`; before every sync, confirm it is the same agent-created scratch directory. Use incremental `robocopy /E /XJ /COPY:DAT /R:1 /W:1` with `/XD .git .venv .pytest_cache .ruff_cache .tmp_pytest test-run-temp config_backup logs .superpowers theme_pack_weight .Jules __pycache__ .tmp_pycache_codex_2026_11_12_compile1 .tmp_audit_workspace_2026_11_12_run1` and `/XF config.yaml* theme_pack_list.yaml`. Never read or copy personal configuration or backup contents. If a source file is deleted later, verify and remove only that exact stale copy path inside the known scratch directory.

- [ ] **Step 2: Run syntax and collection baseline**

From the disposable copy, run `E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany\.venv\Scripts\python.exe -X pycache_prefix=.tmp_pycache_codex_2026_11_12_compile1 -m compileall -q app module tasks utils scripts main.py main_dev.py updater.py`.

From the disposable copy, run `E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany\.venv\Scripts\python.exe -m pytest --collect-only -q -p no:cacheprovider`.

Expected: report exact exit codes and collection count; do not infer test pass status from collection.

- [ ] **Step 3: Run current test and lint baseline**

From the disposable copy, confirm `.tmp_pytest_codex_2026_11_12_run1` does not exist, then run `E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany\.venv\Scripts\python.exe -m pytest -ra -p no:cacheprovider --basetemp=.tmp_pytest_codex_2026_11_12_run1`. Increment the suffix for later full-suite runs and never reuse an existing basetemp path. Remove only test/bytecode directories created inside the disposable copy after confirming their exact paths.

Run `E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany\.venv\Scripts\ruff.exe check app module tasks utils scripts tests main.py main_dev.py updater.py`.

Expected: record the exact result and any environment limitation. Do not amend tests merely to make the baseline green.

- [ ] **Step 4: Read applicable current evidence**

Inspect the newest useful log by timestamp and sanitized error summaries; inspect current CI, packaging, resource manifests, updater flow, and test coverage. Mark the August 2026 log as historical evidence.

### Task 2: Audit and Repair the Existing Background-Input Changes

**Files:**
- Modify: `module/automation/input_handlers/input.py`
- Modify: `module/game_and_screen/screen.py`
- Modify: `tasks/teams/team_formation.py`
- Modify: `module/automation/automation.py` only if the audit proves a caller contract needs correction
- Test: `tests/unit/module/automation/test_input_contract.py`
- Test: `tests/unit/module/game_and_screen/test_screen.py`
- Create directory if absent: `tests/unit/tasks/teams/`
- Create: `tests/unit/tasks/teams/test_team_formation.py`

**Interfaces:**
- Consumes: `_begin_mouse_lease_with_mode(x: int, y: int, lease_mode: str) -> _MouseLease | None`, `Handle.hide_for_background_input()`, `Handle.restore_background_input_visibility(snapshot)`, and `Automation.get_background_input_state()`.
- Produces: exception-safe lease acquisition, bounded screenshot failure, and background-input state based on observable scroll-pane movement.

- [ ] **Step 1: Make existing lease tests model the idle recheck**

Set `_get_last_input_elapsed_ms()` to `600` in `_lease_handler()` and in `test_window_move_input_rejects_driver()`. Keep `test_window_move_begin_lease_rechecks_idle_after_wait()` set to `10`.

Run the current lease contract files in the disposable copy:

`E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany\.venv\Scripts\python.exe -m pytest tests/unit/module/automation/test_input.py tests/unit/module/automation/test_input_contract.py -k "not restores_state and not activation_raises" -q -p no:cacheprovider --basetemp=pytest-existing-lease-contracts1`

Expected: the 7 baseline lease failures pass; the low-elapsed-time rejection test still verifies that a genuinely recent user input cancels acquisition.

- [ ] **Step 2: Add lease-acquisition exception tests**

Add `test_window_move_begin_lease_restores_state_when_position_set_raises_after_move` and `test_window_move_begin_lease_restores_visibility_when_activation_raises`.

The position-set test must simulate a partial move before raising, then assert the original rect, visibility snapshot, and foreground are restored. The activation test must assert position and visibility are restored when activation raises.

- [ ] **Step 3: Run the new lease exception tests**

Run only the new exception tests in the disposable copy with a new basetemp path.

Expected: the partial-position-move case fails because acquisition has no enclosing rollback.

- [ ] **Step 4: Add layered-state failure tests**

Extend `tests/unit/module/game_and_screen/test_screen.py` with failed `GetLayeredWindowAttributes`, false restore API result, exact layered color-key preservation, and “layered is not click-through” cases.

Assert that unreadable pre-existing layered state prevents a transparent lease, color key/alpha/flags are restored exactly, false native API results remain failures, and applying `WS_EX_LAYERED` without `WS_EX_TRANSPARENT` does not set `isTransparent`.

- [ ] **Step 5: Implement exception-safe acquisition**

In `_begin_mouse_lease_with_mode`, capture the original window rect before the move attempt. Wrap the post-hide acquisition steps so exceptions restore that rect, any captured visibility, and original foreground before returning or re-raising the established failure result. Do not depend on `_set_window_pos` returning its old rect when that call itself raises.

- [ ] **Step 6: Bound team-selection screenshot waits**

Add `test_team_selection_initial_screenshot_timeout_stops`, `test_team_selection_post_scroll_capture_timeout_stops`, `test_clean_team_returns_false_after_bounded_attempts`, `test_team_formation_stops_when_clean_team_fails`, and `test_load_team_code_capture_failure_stops`.

Use one bounded screenshot helper for team selection, team clearing, formation, and team-code capture points; return a clear failure after 3 failed capture attempts. Bound the `clean_team()` state loop to 30 attempts and make its caller stop if the clear state cannot be reached.

- [ ] **Step 7: Verify scroll state rather than capture availability**

Add `test_scroll_pane_changed_ignores_pixels_outside_team_list`, `test_team_selection_scroll_verification_uses_visible_fallback`, `test_team_selection_at_top_without_movement_is_accepted`, and `test_team_selection_no_observable_scroll_stops`. A captured frame alone or unchanged scroll-pane region must not transition `background_input_state` to `supported`.

Add `_scroll_pane_changed(before: Image.Image, after: Image.Image, region: tuple[int, int, int, int]) -> bool` and compare the same scrollable-pane region before and after input, excluding fixed UI chrome. For `scroll_to_top`, unchanged content is accepted only if OCR identifies the first row in the top-row band. Otherwise set the backend to visible fallback, retry once through that mode, and stop explicitly if movement remains unconfirmed.

- [ ] **Step 8: Implement and rerun focused tests**

Implement the smallest changes in `team_formation.py` that satisfy the new tests, preserve the existing drag fallback contract, and bound the visible-mode retry to one attempt.

Synchronize the source into the verified `E:\PUBLIC\Project\AALC\.codex_test_workspace_2026_11_12_run1` copy, confirm `pytest-team-input-focus1` does not exist, then run `E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany\.venv\Scripts\python.exe -m pytest tests/unit/module/automation/test_input.py tests/unit/module/automation/test_input_contract.py tests/unit/module/game_and_screen/test_screen.py tests/unit/tasks/teams/test_team_formation.py -q -p no:cacheprovider --basetemp=pytest-team-input-focus1`. Expected: all pass without unbounded loops.

### Task 3: Revalidate Historical Audit Claims Across the Current Fork

**Files:**
- Modify: `docs/audits/2026-11-12-self-audit.md`
- Inspect: `app/`, `module/`, `tasks/`, `utils/`, `scripts/`, `tests/`, `.github/`, `assets/config/`, and packaging files

**Interfaces:**
- Consumes: current source and test evidence plus the reference reports.
- Produces: prioritized findings with path/line, impact, evidence grade, regression test, action, and residual status, incorporating the completed read-only current-fork review.

- [ ] **Step 1: Recheck reported historical defects**

Start from the completed read-only current-fork review, then revalidate its high-impact claims plus historical findings for template matching, route flow, config reset, task cancellation, updater loops, OCR failure handling, and security-boundary violations against current HEAD and current diff.

- [ ] **Step 2: Trace startup-to-task-to-shutdown paths**

Inspect application entry, configuration load/migration, input initialization, screenshot/OCR, task stop/error propagation, resource sync, updater, and packaging.

- [ ] **Step 3: Inventory unbounded retries and exception boundaries**

Search current Python sources for loops around screenshot absence, polling without deadlines, broad catches that collapse errors into empty results, forced thread termination, and input/window operations lacking `finally` restoration.

- [ ] **Step 4: Audit user-visible Mirror paths**

Review route choice, shop fusion, EGO gift selection, failed recognition, retry bounds, cancellation, and restart/recovery. Test only claims that can be reproduced with deterministic fixtures or mocks.

- [ ] **Step 5: Add confirmed findings to the repair queue**

For every confirmed P0/P1 finding, define a focused regression test and repair step before moving to documentation cleanup. For P2 findings, record evidence, impact, and a disposition.

### Task 4: Repair Cooperative Stop and UI Shutdown

**Files:**
- Modify: `tasks/base/script_task_scheme.py`
- Modify: `tasks/base/task_engine.py`
- Modify: `app/farming_interface.py`
- Modify: `app/my_app.py`
- Modify: `tasks/tools/infinite_battle.py`
- Modify: `tasks/tools/production_module.py`
- Create: `tests/unit/app/test_task_stop_lifecycle.py`
- Test: `tests/unit/tasks/base/test_task_engine_stop.py`

**Interfaces:**
- Consumes: `my_script_task.is_stop`, `TaskEngine`'s screenshot stop hook, each tool worker's existing `stop()` method, and Qt `finished` signals.
- Produces: `init_game(thread=None) -> None` with bounded window discovery; `FarmingInterface.stop_script(timeout_ms=2000) -> bool`; close paths that defer exit until worker completion instead of force termination.

- [ ] **Step 1: Add deterministic stop and close tests**

Add `test_init_game_stops_when_worker_flag_is_set_before_window_found`, `test_manual_stop_requests_task_stop_before_simulator_cleanup`, `test_manual_stop_keeps_start_disabled_while_worker_runs`, `test_main_window_close_defers_until_task_worker_finishes`, and `test_tool_window_close_does_not_force_terminate_worker`; no test may invoke a live game or real input.

- [ ] **Step 2: Run the focused tests in the disposable copy**

Synchronize the source into the verified test workspace, then run the exact test nodes with a new basetemp directory.

Expected: tests fail because initialization does not check the stop flag, manual simulator cleanup precedes the stop request, and the main/tool close paths call `terminate()`.

- [ ] **Step 3: Implement cooperative stop ordering**

Pass the optional worker into `init_game`; check its stop flag before initialization and during the existing window-handle wait. Define `WINDOW_HANDLE_INIT_TIMEOUT_SECONDS = 120` and `WINDOW_HANDLE_POLL_INTERVAL_SECONDS = 1`, then raise the existing user-stop or no-window error at the bound.

Set the task stop flag before simulator cleanup. Make `stop_script()` return whether the worker actually finished; keep the UI disabled in a stopping state if it has not finished.

- [ ] **Step 4: Defer window close until workers finish**

On confirmed main-window or tool-window close, request each worker's cooperative stop. Ignore the close event while a worker is still running and reconnect its `finished` signal to retry the close. Remove forced `terminate()` calls from the user-facing close path.

- [ ] **Step 5: Run focused tests**

Expected: every new stop/close test passes, active workers are not replaced while running, and no force-termination method is called.

### Task 5: Contain Resource and Updater Manifest Paths

**Files:**
- Modify: `module/resource_sync/manifest.py`
- Modify: `module/resource_sync/service.py`
- Modify: `updater.py`
- Create directory if absent: `tests/unit/module/resource_sync/`
- Create: `tests/unit/module/resource_sync/test_manifest_paths.py`
- Modify: `tests/unit/updater/test_updater_bounds.py`

**Interfaces:**
- Consumes: remote `ResourceFileEntry.path`, extracted resource members, and updater `changes.json` paths.
- Produces: normalized manifest-relative paths and resolved destinations proven to remain inside the intended asset or installation root.

- [ ] **Step 1: Add failing resource manifest tests**

Add `test_resource_file_entry_rejects_parent_traversal_paths`, `test_resource_file_entry_rejects_absolute_and_drive_paths`, `test_resource_package_entry_rejects_unsafe_paths`, and `test_resource_sync_never_copies_or_deletes_outside_assets_root`.

The tests must use temporary directories and prove the external sentinel file remains byte-identical.

- [ ] **Step 2: Run the new tests in the disposable copy**

Expected: the `../outside.txt` probe currently passes model parsing and the service can derive a path outside the asset root.

- [ ] **Step 3: Validate manifest paths at construction and at file operations**

Add `_validate_manifest_relative_path(value: str) -> str` in `module/resource_sync/manifest.py` and apply it to file and package entries; reject empty, absolute, drive-qualified, and parent-traversal paths. Resolve extracted and target paths and verify they remain under their respective roots immediately before copy or delete.

- [ ] **Step 4: Add failing updater path tests**

Add `test_normalize_manifest_path_rejects_parent_traversal_and_absolute_paths` and `test_incremental_update_never_removes_outside_install_root`.

- [ ] **Step 5: Implement updater path containment**

Update `_normalize_manifest_path()` and the delete/copy call sites to reject paths that resolve outside `cover_folder_path`, including Windows drive and separator forms.

- [ ] **Step 6: Run focused tests**

Expected: traversal/absolute paths fail before filesystem mutation; valid nested relative paths still update correctly; sentinel bytes outside each root remain unchanged.

### Task 6: Make Input Coordinates and Timing Deterministic

**Files:**
- Modify: `module/automation/automation.py`
- Modify: `module/automation/input_handlers/simulator/__init__.py`
- Create: `tests/unit/module/automation/test_input_policy.py`
- Modify: `tests/unit/module/automation/test_input.py`

**Interfaces:**
- Consumes: detected coordinates, configured `mouse_action_interval`, and simulator swipe endpoints/speed/minimum spacing.
- Produces: exact detected click coordinates, fixed configured action timing, and repeatable simulator swipe points.

- [ ] **Step 1: Add failing tests**

Add `test_calculate_click_position_preserves_detected_coordinates`, `test_mouse_action_interval_is_deterministic`, `test_insert_swipe_is_repeatable_and_preserves_endpoints`, and `test_insert_swipe_respects_minimum_spacing`.

- [ ] **Step 2: Run the focused tests in the disposable copy**

Expected: the click-coordinate and interval tests expose `np.random.normal`; repeated `insert_swipe()` calls produce different paths.

- [ ] **Step 3: Implement deterministic behavior**

Remove the evasion-specific random offset and random interval from `Automation`; retain its existing interval cap and pass the detected point unchanged. Replace randomized simulator Bézier control points/sample bounds with a deterministic path while preserving the function signature, endpoints, and minimum-spacing behavior.

- [ ] **Step 4: Update stale test descriptions**

Rename or rewrite `test_randomize_coords_bounded_offset` and randomization comments to describe deterministic coordinate behavior; do not broaden this change to unrelated random values such as audio selection.

- [ ] **Step 5: Run focused tests**

Expected: coordinate and interval assertions are deterministic across repeated calls; simulator paths preserve endpoints and spacing; unrelated input backend contracts pass.

### Task 7: Bound Screenshot and Window-Initialization Recovery

**Files:**
- Modify: `module/automation/automation.py`
- Modify: `module/game_and_screen/screen.py`
- Modify: `app/tools_interface.py`
- Modify: `tasks/teams/team_formation.py` as described in Task 2
- Test: `tests/unit/module/automation/test_state_flow.py`
- Test: `tests/unit/module/game_and_screen/test_screen.py`
- Create: `tests/unit/app/test_tools_interface_startup.py`

**Interfaces:**
- Consumes: screenshot capture failure, task stop state, window sizing API failures, and tool initialization state.
- Produces: bounded waits with explicit failure outcomes; screenshot failure remains distinguishable from a valid “target not found”.

- [ ] **Step 1: Add deterministic timeout tests**

Add `test_find_element_capture_failure_is_bounded`, `test_take_screenshot_stop_request_interrupts_retry`, `test_set_win_exception_retry_is_bounded`, and `test_tool_startup_returns_failure_after_deadline`.

- [ ] **Step 2: Run the focused tests in the disposable copy**

Expected: the current inner screenshot and window-size exception loops do not meet the new deadline/stop contracts.

- [ ] **Step 3: Implement bounded recovery**

Add `stop_check: Callable[[], bool] | None = None` to `Automation.take_screenshot()`. Check it on each internal capture retry and propagate `userStopError`; retain one automatic game restart after the existing 60-second failure period, then raise an explicit screenshot error. Replace nested `find_element()` screenshot `while` loops with a bounded failure path.

Cap `Screen.set_win()` verification at 5 attempts with a 1-second interval and explicit failure. Give `_tool_start()` a 10-second initialization deadline while continuing to process Qt events.

- [ ] **Step 4: Run focused tests**

Expected: each failure terminates within its configured bound; successful screenshots and successful tool/window initialization preserve the current behavior.

### Task 8: Make OCR Failures Observable

**Files:**
- Modify: `module/ocr/ocr.py`
- Create directory if absent: `tests/unit/module/ocr/`
- Test: `tests/unit/module/ocr/test_ocr.py`

**Interfaces:**
- Consumes: valid empty OCR output, malformed image input, and engine exceptions.
- Produces: `OCR.run(image) -> RapidOCROutput` for valid input, including no-text recognition; raises `OCRExecutionError` with the original cause for conversion or engine failure.

- [ ] **Step 1: Add tests for empty results and failures**

Add `test_ocr_empty_text_returns_empty_output` and `test_ocr_engine_failure_raises_ocr_execution_error`.

- [ ] **Step 2: Run tests to observe current conflation**

Expected: no-text returns a valid empty output; the engine-error test fails because the current code also returns an empty output.

- [ ] **Step 3: Implement explicit OCR failure behavior**

Add `OCRExecutionError(RuntimeError)` and raise it from conversion/engine failures with the original cause. Let existing task-level error handling surface the failure and safely stop the current task.

- [ ] **Step 4: Run focused tests and adjacent OCR consumers**

Expected: no-text callers keep the existing output contract; actual OCR failures become explicit task errors.
