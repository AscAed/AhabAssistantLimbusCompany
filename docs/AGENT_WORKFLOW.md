# Agent Workflow

## Initialization

1. Read `AGENTS.md` if present and applicable `.agents/rules/`; local instructions may be excluded from commits.
2. Read this index, [project facts](PROJECT.md), the [architecture overview](architecture/overview.md), and [development and validation](development/environment-and-validation.md).
3. Inspect `git status --short --branch`, recent commits, the complete diff for target files, relevant tests, and the newest useful sanitized log summary.
4. Record the existing modified and untracked paths before editing. Treat all of them as user-owned until their role is established.
5. Read the current audit before relying on a historical issue list. Never copy raw logs into committed documentation.

## Change Rules

- Keep edits within the request and existing module boundaries. Prefer current helpers and APIs.
- For behavior changes, add a focused regression test first, observe its expected failure, then implement the smallest fix.
- Do not delete a module, asset, workflow, ignored directory, or historical note based on age or name. Trace callers, configuration references, packaging, tests, and history first.
- Do not inspect or copy personal `config.yaml`, `config_backup`, raw logs, or runtime data into test artifacts or documentation.
- Keep reference repositories read-only. Cite their exact local commit and source paths.
- Do not implement detection evasion, behavioral impersonation, packet tampering, process or memory bypass, or weakened security controls. Work on stable input delivery, diagnosable failures, bounded retries, cooperative stop, and testability.
- Do not interact with the live game as a test. Use offline fixtures and fakes.

## Validation and Git

- Run the smallest relevant regression suite, then compile, full pytest, and Ruff when the change warrants it.
- Keep pytest temporary directories unique per run. If sandbox access blocks temporary-directory setup or cleanup, use a separate authorized scratch path and record that limitation; do not change ACLs.
- Inspect the final diff, untracked paths, ignored outputs, and sensitive-file boundary before staging.
- Commit only reviewed task files. Do not push, publish, merge, or open a PR unless remote integration is needed and separately verified.

## External Network Commands

When the local Clash proxy is available at `127.0.0.1:7897`, set its proxy variables in the same PowerShell invocation as an external network command. Otherwise use your environment's configured proxy or connect directly:

```powershell
$env:http_proxy = "http://127.0.0.1:7897"
$env:https_proxy = "http://127.0.0.1:7897"
$env:all_proxy = "socks5://127.0.0.1:7897"
git fetch origin
```

Local file inspection, offline tests, and local builds do not need a proxy.
