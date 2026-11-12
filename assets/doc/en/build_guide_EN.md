## Build Guide

Use Windows with the Python 3.12 CI baseline and install the locked dependencies:

```powershell
uv sync --frozen
```

The release build creates both the application and updater, copies assets, and writes an archive:

```powershell
uv run python scripts/build.py --version 1.0.9
```

The build script recursively removes `dist/` at startup. Verify that directory is absent, or build in a disposable copy without user artifacts. The script also requires `7z` on `PATH`. Keep generated build outputs out of Git.

See the [development guide](../zh/develop_guide.md) and [documentation index](../../../docs/INDEX.md) for validation and project boundaries.
