# Current Self-Audit

Date: 2026-11-22. Repository: `E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany`. Base commit: `cc9e3724876b81be7bbb201c1bb25d2d008c5c57` on `main`; `origin/main` matched at inspection. Validation used a disposable source snapshot of the then-current worktree without `.git`, the local virtual environment, personal configuration, logs, caches, or protected temporary directories. Results below apply to that source/test snapshot, not to an installed application.

## Workspace and References

- The repository had one registered worktree and one local branch (`main`). The fork's GitHub branch listing contained only `main`; the previously identified Jules feature branch was deleted at the user's direction. No associated PR was found during the earlier branch cleanup. The `upstream/*` refs are source-project comparison branches and were retained.
- The user authorized removing the Jules note. The only remaining `.jules/palette.md` diff is removal of its three-line note; this was kept separate from the other source and documentation work until final staging.
- The local AALC reference checkout is clean at `2fcb1b4620108c9bb0cf138f82790dd13f46356c`. Its cached `origin/main` is `ec8aa1750f823f2c5daf76d1807282b17b968a30`, 12 commits ahead; it was not fetched. The clean LALC reference checkout and cached `origin/master` are both `431b432e22f0b0da08b95d7c478fa213be20b3e8`. Reference findings remain limited to those source snapshots.
- The reference reports and [target architecture](../architecture/target-and-optimization.md) distinguish reusable configuration, workflow, and validation ideas from implementation details that are not compatible drop-ins. No reference code was copied in this batch.

## Source Review and Repairs

- Reviewed the in-flight changes across configuration/UI contracts, screenshot and page-state recognition, retry/stop behavior, Mirror entry/shop/recovery result propagation, process-name matching, updater path handling, and log redaction. The changes stay within existing PySide6, task, and automation boundaries.
- Confirmed a new unbounded failure path in `lunacy_to_enkephalin()`: repeated `take_screenshot() is None` continued the loop without consuming a purchase attempt. Added five stop-aware capture attempts with short waits and an explicit failure before confirmation input. Added regression coverage for persistent failure and transient recovery.
- Existing changes also bound persistent title-screen and simulator-start retries; propagate failed Mirror helper results to the task boundary; verify the route-map state after theme selection; prevent invalid process-name substring matches; remove team codes and signed request URLs from logs; and cover opening-EGO slot orders and the shop fusion prompt.
- No additional component was removed. The audit did not establish a safe unused/deprecated module or dependency deletion.

## Dependencies and Build

- `uv lock --check --offline` passed and resolved 251 locked packages.
- `uv pip check --offline` reports one metadata incompatibility: RapidOCR 3.4.1 declares `opencv-python>=4.5.1.48`, while this project installs `opencv-python-headless 4.11.0.86` under an existing `uv` override. Both `rapidocr` and `cv2` import successfully (`cv2 4.11.0`). Do not install both OpenCV distributions or change the override without a packaging/runtime comparison.
- Full project Ruff and `compileall` passed on the isolated snapshot.
- After the visual-fixture and Grandet follow-up, the full worktree suite passed **615 tests, 2 skipped** in 75.17 seconds. The skips require Windows symbolic-link creation, unavailable in this environment. The earlier isolated-snapshot run took 127.85 seconds and predates the Grandet follow-up.
- After the PR #143 review fixes, the current worktree suite passed **620 tests, 2 skipped** in 76.36 seconds. The two skips require Windows symbolic-link creation. The focused Enkephalin and theme-pack recovery files passed **39 tests**. Full-project Ruff, compileall, and `git diff --check` passed against the final source/test diff.
- `scripts/build.py --version audit-20261122` built both PyInstaller targets from the code tree later committed as `9480845`, before the Grandet review follow-up. The build used Python 3.12.13, PyInstaller 6.16.0, and the repository's 7-Zip 23.01 binary; it generated 538 translations. Independent archive test and extraction passed: 204 folders, 1,542 files, 354,657,133 uncompressed bytes. All 688 asset paths matched; the only hash difference is build-injected `assets/config/version.txt`. This does not validate the latest PR head; its Windows CI build remains pending.
- Archive SHA-256: `73FDDA81FFBD832B1D7C7224F1E4CCB02DCD1668D41BBF2695928A5F40681BA2`. Extracted app SHA-256: `F291AF81A1591F44D34B20383E840062FA4A976CD789C66B28DC17A17809A766`. Extracted updater SHA-256: `E852A7F3C03534B617CDCA78785B9ECE9115A9EE6DA9550B1E29E69334862494`.
- Build warnings were limited to a third-party PyAutoGUI invalid escape sequence, a non-Windows AppKit import notice, and optional PP-OCRv5 models absent from the existing environment. The app and updater were not launched.

## Runtime and Deployment

- A read-only process and uninstall-registry query found no AALC, AALC Updater, legacy Update, AhabAssistant, or LimbusCompany process, and no matching AALC uninstall entry. This does not rule out portable, manually copied, or remote deployments.
- Local `logs/debugLog.log` and `.1` metadata shows last writes on 2026-08-19 and 2026-08-17 UTC. Their contents were not read for this audit. They are historical local data, not current runtime evidence.
- No app startup, updater execution, game automation, or deployment operation was performed. The archive is a build artifact, not an installed or released package.

## Pass UI Evidence

- **User-confirmed flow:** home-page pass banner to Battle Pass main shows a transition; Battle Pass main to Pass Missions does not; returning from Pass Missions to Battle Pass main shows a transition. Daily, Weekly, and Season tabs inside Pass Missions update the mission list and countdown without a whole-screen transition.
- The user supplied three in-chat screenshots to clarify this behavior. They were not saved as local files, hashed, or used as automated fixtures. `tasks/daily/get_prize.py` already waits for mission-list-region change across fresh frames when changing categories; this matches the described no-transition behavior but does not prove the threshold works for every category, scale, or live capture path.
- Nine user-captured full-frame visual candidates support loaded-page/layout and Mirror anchor regression checks. The user explicitly authorized public repository inclusion when the recognition tests need the samples, so this follow-up includes them as test fixtures. A separate game-content license was not established by the prior policy review; user project authorization and third-party rights are distinct. The generic `pass_coin.png` matcher also matches visibly incomplete rows, so it is not a verified claimability signal. No claimability heuristic was added.
- To qualify reward clicks, collect full-frame PNGs for both Daily and Weekly with manually confirmed incomplete, completed-but-claimable, and already-claimed rows. Keep the selected tab, relevant row evidence, game build if available, capture date, dimensions, and scale in a manifest. Do not crop, resize, or edit tested regions. The game window was not available to this audit, so autonomous capture did not succeed.

## Documentation and Remaining Gates

- `docs/PROJECT.md` is now a concise current-facts and navigation page; [`docs/INDEX.md`](../INDEX.md) points to this audit; the implementation handoff records the new user-confirmed pass transition semantics; and the AALC reference report no longer claims its cached remote ref is current.
- Remaining evidence gaps: RapidOCR/OpenCV metadata reconciliation; labeled pass reward states and a no-claim result policy; visual coverage of Season, post-keyword fusion, and other live states; current-package startup/normal-exit and updater qualification; installed/deployment identity; and separate rights-holder authorization for public distribution of game-content screenshots.
- The protected `.tmp_pytest/` and `test-run-temp/` paths were not read, deleted, or ACL-modified. The disposable validation/build outputs are outside the repository worktree.
