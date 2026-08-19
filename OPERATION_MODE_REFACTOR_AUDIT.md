# Operation Mode Refactor Audit

## Purpose

This document records the implementation baseline for replacing the legacy Windows
operation modes with two user-facing modes:

- `foreground_mouse`: foreground operation that moves the physical mouse and favors speed.
- `background_window`: background operation that moves the game window and does not move the physical mouse.

The supplied UI screenshot is evidence of the legacy three-option UI, not an independent
implementation instruction. The user-defined semantics and repository rules are the source
of truth.

## Baseline Findings

- `module/automation/automation.py` previously selected `Input`, `BackgroundInput`, or
  `WindowMoveInput` from `win_input_type`.
- `background_click` was a second, derived-but-persisted switch used by screenshots, window
  placement, transparency, foreground activation, and task branches.
- `BackgroundInput` sent Win32 messages but could call `SetForegroundWindow` and
  `SetCursorPos` during active drags, so it did not satisfy the new non-interference contract.
- `WindowMoveInput` already implemented the main window-transaction idea, but scrolling was
  unsupported, physical input drivers could move the cursor, and several operations restored
  the window only on the success path.
- `tasks/teams/team_formation.py` selected a backend by class-name string and directly used
  hardware wheel APIs, bypassing the input abstraction.
- `module/automation/screenshot.py` and `module/game_and_screen/screen.py` coupled behavior to
  `background_click`, making the persisted boolean a hidden runtime mode selector.
- Historical commit `e901940` introduced the current input/vision/state-flow refactor. The
  current repository has already made input timing and coordinates deterministic; no randomized
  input intended to evade security auditing is part of this refactor.

## Configuration Migration

The canonical configuration field is now `operation_mode`:

| Legacy input | Canonical value |
| --- | --- |
| `win_input_type: foreground` | `foreground_mouse` |
| `win_input_type: background` | `background_window` |
| `win_input_type: window_move` | `background_window` |
| `background_click: false` | `foreground_mouse` |
| `background_click: true` or missing legacy mode | `background_window` |

Legacy keys are accepted only while loading an old file. The runtime model and example
configuration expose only `operation_mode`.

Simulator mode remains an independent ADB/MuMu native transport. It is not relabeled as a
Windows mouse-moving or window-moving implementation.

## Current Implementation Status

- Added `migrate_operation_mode()` and bumped the example configuration version to
  `1787011200`.
- Added the two-option UI mapping and updated mode descriptions/translations.
- Runtime selection now chooses foreground mouse input or the window-moving backend from
  `operation_mode`.
- Window-moving mouse operations now use a bounded focus lease: the game window is aligned under
  the unchanged physical cursor, briefly activated, and receives real `SendInput` click/wheel
  signals. Physical input drivers are rejected by design. If Windows' foreground lock rejects
  the first activation attempt, the backend makes one bounded `AttachThreadInput` retry and
  detaches the queues immediately; it never sets TOPMOST or moves the physical cursor.
- Window-moving click/drag/drag-link/scroll operations restore the original position and previous
  foreground window in `finally` blocks; a failed restoration is surfaced as an input failure.
- Team formation scrolling now uses the shared `auto.mouse_scroll()` contract instead of direct
  `SetCursorPos`/`mouse_event` calls.
- Unity follow-up: the real `LimbusCompany` window was inspected on 2026-08-18 and exposed only
  a top-level `UnityWndClass` with no child HWND. Child-window routing is therefore not a reliable
  runtime strategy. Background mouse operations now use a bounded focus lease, keep the physical
  cursor fixed, align the game window under it, inject real mouse input with `SendInput`, and restore
  the previous foreground window and game position in `finally` blocks. The lease records the
  original cursor and pause state for observability; it never calls `SetCursorPos`.
- Foreground follow-up: physical mouse movement now uses a direct low-latency move instead of a
  per-point delayed Bezier path; simulator input remains unchanged.

## Risks and Follow-up Work

1. Remove or isolate the legacy `BackgroundInput` implementation after all compatibility tests
   are migrated; it must never be selected by runtime code.
2. Validate the short focus lease on a real Windows desktop while another window is foreground;
   unit tests cover activation, the foreground-lock retry contract, SendInput sequencing, idle
   gating, and restoration.
3. Validate background-mode Toast delivery on a real Windows desktop; unit tests currently
   cover the failure routing without starting the application UI.
4. Keep simulator ADB/MuMu transport tests separate from Windows operation-mode tests.

## Verification Baseline

- Before this refactor, the focused Windows input contract suite passed 39 tests.
- Migration tests cover both canonical values, all legacy values, missing values, and invalid
  explicit values.
- New background scroll and physical-driver rejection tests pass locally.
- Final local verification: the focused input suite passed 53 tests and the full suite passed 126 tests
  using a writable temporary directory;
  `uv run ruff check .` passed. Pytest emitted only the repository's known `.pytest_cache`
  permission warning when that cache directory is unavailable.

## 2026-08-19 Final Implementation Update

**_window_move_to Fix**: Changed return type from `tuple[int, int]` to `bool` and replaced
`raise RuntimeError` with `log.warning + return False` for heartbeat failures during drag
operations. All four call sites (`mouse_drag`, `mouse_drag_down`, `mouse_drag_link` loop
and final segment) now check the return value, allowing the button-release `finally` block
and `_end_mouse_lease` to restore window state before propagating failure to the task layer.

**Implementation Verification**: All requirements from "Unity 后台输入：短暂焦点租约方案" are met:
- Wait for user idle (500ms, max 10s timeout) using GetLastInputInfo
- Move window with SWP_NOACTIVATE | SWP_NOZORDER (no TOPMOST)
- Brief activation with SetForegroundWindow + AttachThreadInput compatibility retry
- SendInput for real mouse events (LEFTDOWN/LEFTUP/WHEEL/MOVE heartbeat)
- Finally block always restores window position and original foreground
- WindowMoveInput never calls SetCursorPos or pyautogui.moveTo
- All mouse operations (click/scroll/drag/drag_down/drag_link) use unified _mouse_lease

**Test Results**: 53 focused input tests passed, 126 full suite tests passed, Ruff clean.


## 2026-08-19 Unity Input Event Processing Fix

**Problem**: After implementing the focus lease, SendInput operations were successful but Unity
did not respond to clicks. Log analysis showed lease_acquired, SendInput ... sent=1 success=True,
and lease_released ... restored=True, but the game remained on the same screen.

**Root Cause**: The implementation was restoring the original foreground window immediately after
SendInput completed. Unity needs a brief window of time while it holds focus to process the input
events. Restoring focus too quickly caused Unity to discard the pending events.

**Fix**: Added INPUT_SETTLE_MS = 50 constant and a corresponding sleep() in mouse_click
after wait_pause() but before exiting the lease context manager. This gives Unity ~50ms to
process input events before the foreground window is restored.

**Verification**: All 126 tests pass, Ruff clean. Real-world testing requires running game.


## 2026-08-19 Mouse Wheel Efficiency and Unity Processing Fix

**Problem 1 - Wheel not processed**: Unity did not respond to wheel events even though SendInput
succeeded. Like the click issue, Unity needs time while holding focus to process input events.

**Problem 2 - Inefficiency**: Team formation scrolled 30 times individually, each requiring a full
lease cycle (wait for user idle → acquire focus → send one wheel → restore). This took ~19 seconds
for 30 scrolls (500ms idle wait × 30 ≈ 15s + overhead).

**Fix 1 - INPUT_SETTLE_MS for wheel**: Added the same 50ms settle delay to mouse_scroll after
SendInput(MOUSEWHEEL) and before exiting the lease context, matching the mouse_click fix.

**Fix 2 - Batch wheel**: Added atch_mouse_scroll(direction, count, x, y) method that sends
multiple wheel events within a single focus lease. Updated 	eam_formation.py to use batch scroll:
- scroll_to_top: 30 individual scrolls → 1 batch of 30 (saves ~29 lease cycles)
- scroll_down: pages×12 individual scrolls → 1 batch (saves ~(pages×12 - 1) lease cycles)
- Expected time reduction: from ~19s to ~1s for 30 scrolls

**Verification**: All 126 tests pass, Ruff clean. Real-world testing requires running game.
