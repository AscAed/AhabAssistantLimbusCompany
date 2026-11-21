# Project Facts

## Identity

- AhabAssistantLimbusCompany (AALC) is a Windows desktop assistant for Limbus Company, maintained as a fork of `KIYI671/AhabAssistantLimbusCompany`.
- This project prioritizes stable, diagnosable automation and user control. It does not implement detection evasion, behavioral impersonation, packet tampering, or process/memory bypass.
- The package version is declared in `pyproject.toml`; repository source, built artifacts, installed copies, and deployment are separate identities.
- The latest checkout-specific audit and verification are in [the current self-audit](audits/2026-11-22-current-self-audit.md). Historical test counts and package hashes in older reports apply only to their named snapshots.

## Runtime and Dependencies

- Supported runtime: Windows, Python `>=3.12`; CI selects Python 3.12.
- `uv` and the committed `uv.lock` manage dependencies. Install with `uv sync --frozen`.
- The UI uses PySide6. Automation uses configured screenshot/input backends, OpenCV/Pillow image processing, and RapidOCR.
- The runtime uses `opencv-python-headless`. RapidOCR's package metadata also requires `opencv-python`; `uv` currently carries an override to avoid installing both distributions. See the current audit before changing this contract.
- Local `config.yaml`, backups, logs, cached resources, and runtime state are user data. Never include them in validation snapshots or commits.

## Module Ownership

| Area | Responsibility |
| --- | --- |
| `app/` | PySide6 interface, task controls, and UI worker lifecycle |
| `module/config/` | Typed configuration, migration, and persistence |
| `module/automation/` | Screenshot coordination, image/text lookup, and input dispatch |
| `module/game_and_screen/` | Game process identity, window geometry, and Win32 visibility state |
| `module/ocr/`, `utils/image_utils.py` | OCR and image recognition |
| `tasks/base/` | Task scheduling, retry, stop, and recovery contracts |
| `tasks/mirror/`, `tasks/teams/`, `tasks/daily/` | Mirror, team, and daily/pass workflows |
| `module/resource_sync/`, `module/update/`, `updater.py` | Resource synchronization and application updates |
| `scripts/`, `main.spec`, `updater.spec` | Maintenance and Windows packaging |

## Development and Validation

Use the [development guide](development/environment-and-validation.md) for setup, tests, lint, build, proxy, and isolated-snapshot instructions. Common commands:

```powershell
uv sync --frozen
uv run python main.py
uv run pytest -ra
uv run ruff check app module tasks utils scripts tests main.py main_dev.py updater.py
uv run python -m compileall -q app module tasks utils scripts main.py main_dev.py updater.py
```

Unit tests must use mocks and offline fixtures. Do not use live game interaction as a validation step. `scripts/build.py` removes `./dist`; build only in a disposable copy with no valuable `dist` directory.

## Current Boundaries

- A passing test, process query, archive hash, or source inspection does not prove live-game behavior, installed identity, packaged startup, or deployment.
- Nine user-captured full-frame samples under `tests/fixtures/visual/` are included by explicit user direction because image-regression tests consume them. A prior policy review did not establish a separate game-content license for standalone public PNG fixtures; see the fixture README and audit for provenance and this remaining rights uncertainty.
- `get_pass_prize()` currently matches the generic pass-coin template, which also appears on visibly incomplete mission rows. Do not treat it as a verified claimability signal; see the [fixture audit](audits/2026-11-13-mirror-fixture-inventory.md) and current self-audit.
- The [implementation roadmap](development/implementation-roadmap.md) owns stage and acceptance status. The [architecture overview](architecture/overview.md) records current module/data flow; the [target design](architecture/target-and-optimization.md) is a proposal. Dated audits and the [implementation handoff](audits/2026-11-14-implementation-handoff.md) retain evidence and history.
