# Architecture Overview

## Main Flow

`main.py` initializes the PySide application and main window. `app/my_app.py` composes the settings, farming, tools, and resource synchronization UI. Task requests are validated in the UI and executed through worker objects that pass into `tasks/base/task_engine.py`.

Configuration loads through `module/config/` from the example schema plus any local user configuration. The example is the distributable template; a user's ignored `config.yaml` is private runtime state.

## Automation Path

Task code calls the `auto` facade from `module/automation`. `Automation` selects an input backend, obtains screenshots, and coordinates image, text, and feature lookup. `module/automation/screenshot.py` routes capture by the configured Windows or simulator mode. `module/automation/input_handlers/` owns foreground, window-lease, and simulator input behavior.

`module/game_and_screen/screen.py` owns the game window handle, geometry, and visibility state. The window-move backend restores position and foreground state when a focus lease ends or fails. Production leases keep the game window visible; the alpha-zero hide helper is not selected until native hit-targeting is verified.

OCR calls route through `module/ocr/ocr.py`; `utils/image_utils.py` owns image loading, cropping, and matching primitives. A valid empty OCR result and an OCR execution error are separate outcomes.

## Task and Resource Boundaries

- `tasks/base/` owns task state transitions, cancellation, retries, and recovery.
- `tasks/mirror/` owns Mirror route progression, shop decisions, and EGO selection.
- `tasks/teams/` owns team selection and formation interactions.
- `module/resource_sync/` checks manifests, plans resource changes, verifies downloads, and applies file operations.
- `module/update/` checks releases; `updater.py` applies downloaded update manifests.
- `scripts/build.py`, `main.spec`, and `updater.spec` produce Windows application artifacts.

Keep UI operations in `app/`, configuration schema and migration in `module/config/`, window/input coordination in their respective `module/` packages, and game-specific decisions in `tasks/`.
