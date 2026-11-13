# Project Facts

## Identity

- Project: AhabAssistantLimbusCompany (AALC), a Windows desktop automation application for Limbus Company.
- This checkout is a maintenance fork. It is a stability and diagnostics project, not a general game AI or a proof of optimal play.
- Observed baseline: branch `codex/project-maintenance-2026-11-12`, based on `fe50f94d8b55e953f73f6f3eb0bd2baceb770ead`; audit date 2026-11-12.
- Declared package version at the baseline: `1.0.9` in `pyproject.toml`.

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
- See [the dated self-audit](audits/2026-11-12-self-audit.md) for current verified findings and open limitations.
- The later [documentation investigation](audits/2026-11-12-documentation-baseline.md) names the examined `dc7339fb` checkout and deployment evidence gaps. The [target design](architecture/target-and-optimization.md) and [roadmap](development/implementation-roadmap.md) are proposals, not implemented capabilities.
