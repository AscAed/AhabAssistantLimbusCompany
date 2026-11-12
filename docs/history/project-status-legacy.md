# Historical Project Status Snapshot

> This file preserves milestone labels from an earlier project summary. Those labels were not independently verified and are superseded by [current project facts](../PROJECT.md) and the [2026-11-12 audit](../audits/2026-11-12-self-audit.md).

## Architecture
The game automation engine consists of:
- **Input System (`module/automation/input_handlers/input.py`)**: Win32 and PyAutoGUI input wrapper. Handles mouse clicks, drags, keyboard input, and background messages.
- **Vision System (`module/automation/automation.py`)**: Core automation class. Manages screenshots and template matching.
- **State Control Flow (`tasks/mirror/mirror.py`)**: Main loop for the Mirror dungeon tasks.
- **Shop & EGO Logic (`tasks/mirror/in_shop.py`)**: Logic for buying, enhancing, and fusing gifts.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | R1: Low-Level Input | Input-handler refactor. | none | Historical status claim; not current evidence. |
| 2 | R2: Vision Recognition Optimisation | Implement ROI boundaries, location matching cache, and fast template/color checks. | none | DONE |
| 3 | R3: Lightweight State Control Flow | Refactor Mirror loop to page-based state checker and wait_until_appear dynamic polling. | none | DONE |
| 4 | R4: Shop Fusion & EGO Fixes | Implement grid matching and level indicator checks for fusion and EGO selections. | R2 | DONE |
| 5 | E2E Testing Suite | Create and execute Tier 1-4 tests to verify automation enhancements. | none | Historical status claim; test evidence was not present in this summary. |

## Interface Contracts
### Input Handler
- `Input` / `BackgroundInput`:
  - `mouse_click(x, y, times=1, move_back=True)`
  - `mouse_drag(x, y, drag_time=0.1, dx=0, dy=0, move_back=True)`
  - `mouse_drag_down(x, y, reverse=1, move_back=True)`

### Vision
- `Automation`:
  - `find_element(target, find_type="image_with_multiple_targets", roi=None)`
  - `wait_until_appear(target, timeout=10, poll_interval=0.5)`

## Code Layout
- `module/automation/input_handlers/input.py`
- `module/automation/automation.py`
- `tasks/mirror/in_shop.py`
- `tasks/mirror/mirror.py`
- `tests/`
