# Development and Validation

## Environment

Use Windows and Python 3.12 for the supported CI baseline. The package declares Python `>=3.12`; `.python-version`, `pyproject.toml`, and `.github/workflows/ci.yaml` are the source for the selected environment.

```powershell
uv sync --frozen
uv run python main.py
```

The application performs desktop and game-window operations. Unit tests must use offline fixtures and mocks; do not run the live game as a validation step.

## Checks

```powershell
uv run python -m compileall -q app module tasks utils scripts main.py main_dev.py updater.py
uv run pytest --collect-only -q
uv run pytest -ra
uv run ruff check app module tasks utils scripts tests main.py main_dev.py updater.py
```

When a local ignored `config.yaml` exists, run tests in a disposable source copy that excludes `config.yaml*`, `config_backup`, logs, virtual environments, caches, and runtime data. Importing `module.config` may read the working-directory configuration and create a backup. Never copy the user's configuration into a test copy.

Use a new `--basetemp` for each pytest run. If sandbox restrictions deny listing or cleanup of that temporary directory, request the authorized test execution path; do not alter ACLs or reuse a failed temp path.

## Packaging

The release workflow runs the reusable Windows build after the test job. `scripts/build.py` first removes `./dist`, builds the app and updater, copies assets, and creates an archive. Before running it locally, verify `dist/` is absent or use a disposable copy; do not let the script remove an existing artifact.

The local package build needs PyInstaller and the `7z` executable. A successful source compile or pytest run does not prove the packaged application launches.

The dated [investigation baseline](../audits/2026-11-12-documentation-baseline.md) separates source, historical test/build, and deployment evidence. Future milestone gates and package identity requirements are in the [implementation roadmap](implementation-roadmap.md).

## Network

When available, use the local Clash proxy for external CLI requests in the same PowerShell invocation. Otherwise use your environment's configured proxy or connect directly:

```powershell
$env:http_proxy = "http://127.0.0.1:7897"
$env:https_proxy = "http://127.0.0.1:7897"
$env:all_proxy = "socks5://127.0.0.1:7897"
```

Dependency inspection against an already installed environment can use `uv pip check --offline --python .venv\Scripts\python.exe`. At the 2026-11-12 audit, this reported that RapidOCR metadata requires `opencv-python` while the locked environment uses `opencv-python-headless`; see the audit before changing either distribution.
