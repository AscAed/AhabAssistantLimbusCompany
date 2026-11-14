# Mirror Fixture Inventory

Date: 2026-11-13. Checkout: `codex/project-maintenance-2026-11-12` at `dc7339fb02907d96d56230621fedc896e0e2fa00`.

The inventory below records that initial source snapshot. A current-main continuation is appended after the snapshot findings; do not treat the original test count as the present worktree count.

## Inventory

The core inventory covers tracked test and source paths plus the bundled Mirror image-resource directory. The additional image spot check searches raster filenames under `assets/` and `tests/`. Neither pass inspects local logs, caches, personal configuration, or game data.

| Area | Verified contents | Evidence limit |
| --- | --- | --- |
| Mirror unit tests | 25 tests in five files: shop basics (7), shop capture recovery (1), EGO gift selection (2), road branches (14), and team-selection recovery (1). | These tests use mocks and synthetic data; they are not captured gameplay evidence. |
| Test image fixtures | No `.png`, `.jpg`, `.jpeg`, `.bmp`, or `.webp` files are present under `tests/`. | No visual decision, coordinate, layout, or scroll behavior can be qualified from a real frame in this checkout. |
| Bundled Mirror image resources | 250 files under `assets/images/default/share/mirror`: `claim_reward` 9, `get_reward_card` 7, `road_in_mir` 31, `road_to_mir` 57, `shop` 137, `theme_pack` 5, plus one each for `infinity_mirror_assets.png`, `infinity_mirror_close_assets.png`, `mybus_default_distance.png`, and `mybus_maximum_distance.png`. | These are runtime recognition templates/crops, not full-screen captured-state fixtures. Their presence does not verify recognition against a current game layout. |

## Broader Image Spot Check

A repository-wide filename sweep found 644 raster image files under `assets/` and `tests/`. Spot checks of likely high-resolution candidates found:

- `assets/doc/image/main_page.png` is a screenshot of the AALC application interface.
- `assets/doc/image/theme_list.png` shows configuration text.
- `assets/images/default/share/mirror/shop/fuse_gift_assets.png` is a recognition target on a 2560x1440 canvas, with only a small gift icon visible; canvas dimensions alone do not make it a gameplay screenshot.

These checks do not inspect local logs, caches, personal configuration, or game data, and they do not establish the contents of every raster file. No representative full-frame Mirror gameplay capture was identified in the checked sources. The tests tree has no raster fixture at all.

## Existing Coverage

- `tests/unit/tasks/mirror/test_in_shop_basics.py` checks shop configuration, coordinate sorting/deduplication/filtering, a no-gift path, and the existing bounded `wait_for_screenshot()` helper. The helper is tested for eventual success and for raising after a caller-specified attempt limit.
- `tests/unit/tasks/mirror/test_mirror_ego_gift.py` covers the `type=2` refusal route and persistent screenshot failure before normal selection input. The normal card-ranking and selection loop is not covered.
- `tests/unit/tasks/mirror/test_search_road_branches.py` checks route-control branches, mocked detector results, and screenshot failure. Its route cases pass `numpy.zeros((1080, 1920, 3))` while mocking recognition functions; this validates control flow, not image recognition.
- `tests/unit/tasks/mirror/test_team_selection_recovery.py` covers screenshot failure after team selection, before the dreaming-star/coin entry detector can continue into later actions.
- `tests/unit/tasks/mirror/test_shop_capture_recovery.py` covers persistent screenshot failure in `Shop.heal_sinner()` before any healing action.
- Relevant implementation entry points are `Mirror.acquire_ego_gift()` in `tasks/mirror/mirror.py`, shop fusion and purchase paths in `tasks/mirror/in_shop.py`, and road route detection in `tasks/mirror/search_road.py`.

## Verified Gaps And Next Batch

`Mirror.acquire_ego_gift()` originally looped immediately when `auto.take_screenshot()` returned `None`. Unlike `search_road` paths, this branch had no retry bound. The current working tree now calls the already imported `wait_for_screenshot()` helper, which retries up to its configured limit and raises `RuntimeError` on persistent capture failure. The regression confirms the failure propagates before selection input. This fixes a source-level reliability gap; no runtime incident or live-game behavior was observed.

`Mirror.select_mirror_team()` had a second screenshot failure path: a `None` capture continued before decrementing its recognition counter. It now calls `wait_for_screenshot()` and propagates the helper's bounded failure. The regression failed against the old implementation, then the complete Mirror suite passed with 24 tests. This verifies the capture-failure boundary only; normal team entry and recognition accuracy remain unverified.

`Shop.heal_sinner()` had the same unbounded retry shape: when `auto.take_screenshot()` returned `None`, it continued before decrementing its loop counter. It now calls `wait_for_screenshot()`. The new regression failed against the old loop, then the full Mirror suite passed with 25 tests. This verifies only the capture-failure boundary; healing recognition and coordinates remain unverified.

The capture-failure boundaries are complete without a visual fixture. Keep card ranking, target coordinates, OCR decisions, team recognition, and layout support unchanged until sanitized full-frame fixtures exist.

For later visual batches, collect only approved, sanitized full frames and record the UI state, resolution/window scale, capture provenance, expected detections, and annotated target regions. Keep fixture-backed recognition assertions separate from pure mocked route/fusion logic. If representative frames remain unavailable, label layout, scrolling, and coordinate claims unverified.

## Verification Commands

- `rg -c "^def test_" tests/unit/tasks/mirror` reported 7, 1, 2, 14, and 1 test function in the five Mirror test files.
- `python -m pytest -q -p no:cacheprovider tests/unit/tasks/mirror` passed: `25 passed in 2.27s` in an isolated source copy with the project `.venv` interpreter.
- `rg --files tests | rg -i "\.(png|jpg|jpeg|bmp|webp)$"` returned no image paths.
- A recursive file count under `assets/images/default/share/mirror` reported 250 files with the group counts above.

## Current Worktree Continuation

Date: 2026-11-13. Source HEAD: `main` at `895c8bbe539a7f6ab30507bdc73093824d98453d`; this worktree also contains uncommitted documentation and regression changes.

The current Mirror test tree has **39 collected test cases across 35 test functions** in five files: shop basics (16 functions, 20 cases), shop capture recovery (1), EGO gift selection (2), road branches (14), and team-selection recovery (2). Twelve previously unbounded screenshot-`None` loops in `Shop` now call the shared bounded helper. Aggressive-fusion result handling also stops after 15 no-match iterations. Mock regressions cover these new bounds across EGO power-up, buying, fusion entry/selection/results, selling, enhancement and shop entry/exit. The shop basics file passed **20 tests**; the complete Mirror subset passed **39 tests in 2.21s**.

This does not establish which gifts are detected or selected correctly, coordinate accuracy, normal/system fusion outcomes, UI recovery after three gifts have already been selected, or behavior across resolutions and layouts. One raw screenshot-`None` check remains inside the finite four-attempt aggressive-fusion grid scan. The shared helper limits attempts but does not enforce a wall-clock deadline. No representative full-frame gameplay fixture is present under `tests/`.

The full offline worktree suite after this continuation collected **302 items** and completed with **300 passed, 2 skipped in 25.20s**. The skips are Windows symlink-creation cases. Full-repository Ruff passed. These checks qualify the mocked failure paths and offline code only, not live-game behavior.

## Orchestration Capture Continuation

Date: 2026-11-13. Source HEAD remains `895c8bbe539a7f6ab30507bdc73093824d98453d`; the working tree has further uncommitted capture-boundary and test changes.

Eight previously unbounded screenshot-failure continues in `Mirror` orchestration now use the bounded waiter. Reward-card and theme-pack selection use it as well. Nine new tests cover those terminal paths and confirm no later input is sent after a mocked capture timeout. The full Mirror test tree now has **48 cases across 44 test functions in six files**: shop basics (16 functions, 20 cases), Mirror capture recovery (9), shop capture recovery (1), EGO gift selection (2), road branches (14), and team-selection recovery (2). All 48 passed in 1.99s.

Existing finite loops remain local: observation-gift scan is bounded to 12 attempts and transition confirmation to five; the search-road fallback checks the freeze/restart timeout before its capture retry; initial route-search capture failures return `False`; aggressive-fusion grid scan is bounded to four attempts. The helper's 300-attempt cap is not a wall-clock deadline, and native capture may block within an attempt.

The latest full offline suite collected **311 items** and completed with **309 passed, 2 skipped in 22.70s** using the authorized path in a disposable copy. Both skips require Windows symlink creation. Full Ruff, targeted `compileall`, and `git diff --check` passed. No visual recognition, coordinate, layout, live-game or package-launch claim is established by these mocks.

## 2026-11-14 Continuation: Aggressive Fusion Anchor

An offline mocked path in `Shop.fuse_gift()` showed that aggressive fusion can return from its grid scan without initializing `the_first_line_position`, then continue into ordinary fusion. If ordinary fusion detects any candidate gift, `_processing_coordinates()` compared the y-coordinate to `None` and raised `TypeError`. It now returns no candidates in that state, so no gift-selection click is issued without the required row cutoff.

The regression `test_standard_fusion_skips_candidates_without_aggressive_row_anchor` failed on the old code with the `int >= None` `TypeError`. The updated Mirror unit suite passed **53 tests**, and the current full offline suite passed **360 passed, 2 Windows symlink skips**. This covers a source-level fail-closed boundary only. It does not confirm the row anchor, visual recognition, selection coordinates, or successful fusion on a real game frame. The tests tree still contains no raster gameplay fixtures.

## 2026-11-14 Continuation: Second-System Fusion Flag

`TeamSetting.second_system_action` is a `List[int]`; validation normalizes an enabled boolean to integer `1`. Two `Shop` branches used `is True`, so the configured second-system Level IV mode fell through and fusion entry selected the primary-system keyword. Both checks now accept the typed flag's truth value. Red regressions verified the policy transition and keyword choice failed before the fix.

The Mirror unit suite now passes **55 tests** and the full offline suite passes **362 passed, 2 Windows symlink skips**. These tests exercise typed configuration and mocked control flow only; visual selection and actual fusion remain unverified, and the tests tree still has no representative full-frame gameplay fixtures.
