# Mirror Fixture Inventory

Date: 2026-11-13. Checkout: `codex/project-maintenance-2026-11-12` at `dc7339fb02907d96d56230621fedc896e0e2fa00`.

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
