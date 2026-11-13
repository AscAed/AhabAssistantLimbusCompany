# Cleanup Inventory

Audit date: 2026-11-12. This inventory records evidence-based retention or cleanup decisions. No local cache or runtime directory is assumed to be disposable.

| Candidate | Evidence | Decision |
| --- | --- | --- |
| `AGENTS.md` | Explicitly ignored by the repository `.gitignore`; contains local agent guidance. | Keep local and unmodified. The tracked guide is `docs/AGENT_WORKFLOW.md`. Do not force-add the ignored file. |
| `config.yaml`, `config_backup/`, `theme_pack_list.yaml` | Personal/runtime configuration; values are outside the project source contract. | Exclude from commits and test copies. Do not inspect or delete. |
| `.pytest_cache/`, `.tmp_pytest/`, `test-run-temp/` | Existing paths have access-denied behavior; tests also create temporary files. | Preserve. No ACL change or recursive cleanup. |
| `.venv/`, Python bytecode caches, uv caches | Generated environment state; not application source. | Preserve existing environments; exclude from commits. |
| `tests/unit/module/automation/__pycache__/test_input_contract.cpython-312-pytest-9.1.0.pyc.49100` | 67,884-byte orphaned bytecode temp file; created 2026-11-12 02:57, before the source test's 04:36 update. SHA-256 `7F7F0AF20B732DE417B51CE84ACCF071546E0D2948A44F8AC651DF011D899A35`. | Removed this exact generated file; retained the cache directory and all other cache contents. |
| Legacy test copy ending `_run1` | It contained `config.yaml` when discovered, despite its earlier exclusion plan. | Do not read, reuse, overwrite, or delete; left untouched. |
| Test copies ending `_run2` and `_run3` | Created from a source copy that excluded configuration. `pytest` later created local config/backup data and the final build produced local outputs; no contents of generated configs were read. | Cleanup was attempted at the exact paths, but Windows denied removal of pytest basetemp subdirectories and approval review rejected recursive removal. Leave them in place; no ACL changes or forced deletion. |
| Test copy ending `_run4` | Created on 2026-11-12 from the current source while excluding `AGENTS.md`, `config.yaml*`, `config_backup`, `theme_pack_list.yaml`, logs, caches, and the source virtual environment. Pytest generated local config/backup state. The copy also contains final pytest basetemps, a local offline uv cache, the verified `1.0.9` build/archive, build logs, and temporary `tools/7z.exe`. | Preserve for now. No generated configuration contents were read. Recursive deletion was not attempted after the equivalent earlier cleanup was rejected; remove only after explicit authorization and exact-path review. |
| `logs/` | Historical runtime data, last observed update 2026-08-20. | Preserve locally; use only sanitized summaries. |
| `dist/`, `build/` | Not present in the source checkout at audit. | No cleanup required. Build validation must run in a disposable copy because `scripts/build.py` removes `dist/`. |
| `BackgroundInput` and compatibility backends | Existing code still has callers/tests; no complete removal proof was established. | Retain. Review usage and packaging before any future deprecation. |
| Old root audit and project summaries | Their statuses and test totals are dated and duplicate current facts. | Mark or redirect them as historical; retain unique historical evidence under `docs/history/`. |
| `docs/superpowers/` plan/spec drafts | Generated during the interrupted task; the spec's initial “not approved” status and unchecked steps no longer describe the completed work. | Preserve as archived task context with a superseded-status notice; `docs/audits/2026-11-12-self-audit.md` is the current result source. |
| `tests/test_batch_scroll_fix.py` | Initial Ruff run found import ordering and one unused import; the public backend binding checks remain useful. | Keep the tests, remove the unused import, and sort imports. Final Ruff run passes. |
| OpenCV distribution pair | `uv pip check --offline` reports RapidOCR requires `opencv-python`, while the locked runtime installs `opencv-python-headless`; `cv2` imports work in this environment. | Do not install both or change the lock without a packaging compatibility investigation. Record as unresolved dependency metadata mismatch. |

No directory-wide deletion or broad cache cleanup was performed.
