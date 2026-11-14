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

## 2026-11-14 Reference Image Review and Collection Plan

Scope: read-only filename and image-dimension scan of the two local reference checkouts, with visual spot checks of the specific files below. Current fork HEAD was `d6c481df`; no game, application, build or capture was run. This is not a content review of every image. The user permits saving, sharing and repository inclusion of suitable samples; verify privacy and the rights of each third-party asset before copying it. No image was copied in this batch.

| Source and path relative to reference root | Dimensions and observed content | Classification and suitability |
| --- | --- | --- |
| AALC `2fcb1b4620108c9bb0cf138f82790dd13f46356c`: `assets/images/default/share/mirror/shop/fuse_gift_assets.png` | 2560 x 1440 canvas showing a small gift icon. | Recognition template on a large canvas, not a full gameplay frame. Useful as a target reference only; game version, original capture and redistribution rights unknown. |
| AALC: `assets/doc/image/main_page.png` | 960 x 690 annotated AALC settings UI in Chinese. | Application tutorial, not a game frame. Not suitable for Mirror visual acceptance; provenance and rights remain unverified. |
| LALC `431b432e22f0b0da08b95d7c478fa213be20b3e8`: `lalc_backend/img/zh/mirror/fuse_ego_gift.png` | 227 x 35 Chinese fusion label. | Cropped recognition template, not a full frame. May inform target labeling; game version and redistribution rights unknown. |
| LALC: `img/tutorial_1_07.png` | 2000 x 1125 tutorial composition with LALC UI and an English game panel, crossed by red arrows. | Annotated composite; the embedded panel provides context but is not an unmodified full-frame fixture. Original resolution, game version and rights unknown. |
| LALC: `img/video1Pic.png` | 1612 x 938 promotional composite containing text and a partially obscured interface. | Tutorial/video artwork, not a usable game frame. Source and rights unverified. |

The dimension scan enumerated 650 AALC raster paths, 649 readable by `System.Drawing`, with 267 at least 1280 x 720; `assets/app/sinner/Meursault/Sinner.png` was unreadable by that decoder and its contents were not inferred. It enumerated 761 LALC raster paths, all readable by that decoder, with 66 at least 1280 x 720. Large dimensions do not establish full-frame content: AALC includes templates on large canvases; LALC large candidates include repeated tutorial images under `img/`, `doc/img/` and `lalc_frontend/assets/doc/img/`. Other images remain uninspected, including LALC's tutorial and documentation candidates. Both repositories contain AGPL v3 `LICENSE` files; that alone does not prove rights to redistribute embedded game artwork. Check the specific source and applicable rights before repository inclusion.

No reviewed item qualifies as a representative, unmodified complete Mirror gameplay frame with known version and labels. This is a spot-check result, not a claim that every reference image has been examined. Full-frame visual qualification is still blocked.

| Missing state | Human collection or confirmation | System-assisted collection after an authorized session is available |
| --- | --- | --- |
| Team selection | Reach and identify normal, missing-anchor and selected-team states; capture relevant language, resolution and scale. | Capture full frames of the identified states and record dimensions, provenance and expected team/anchor labels. |
| Initial and observed EGO selection | Reach normal, unavailable, last-scroll and confusing-gift states; identify intended targets. | Capture successive full frames and label visible target regions and expected no-match outcomes. |
| Shop and fusion | Reach normal, empty, selected, missing-anchor and confirmation states; identify the intended gift and expected action. | Capture the prepared states and annotate candidates, row anchors and expected fail-closed outcomes. |
| Route and event | Reach route choices, similar-looking nodes and event transitions; identify the expected route and state. | Capture full frames and label nodes, transitions and expected detections for offline replay. |
| Scrolling and layout | Reach initial, middle, last and no-further-scroll positions, including supported resolution/scale variations. | Capture ordered frames with position metadata; compare detection and coordinates offline. Static images alone do not prove drag effects. |
| Failure and recovery | Identify genuine no-match, loading, disconnection or recovery screens without deliberately damaging user data. | Capture authorized states or use separately labeled synthetic images for control-flow failures; synthetic frames are not evidence of real visual behavior. |

Manual arrival or confirmation is needed to establish that each state and expected label is correct. System-assisted capture is conditional on an authorized game session and a working capture environment; their availability was not established and neither was exercised here. Initial samples should include game version, language, full-frame dimensions, display scale, UI state, source, expected detections and privacy review. Avoid obscuring tested areas; if unavoidable, mark those areas ineligible for acceptance. Preserve mock-only test results separately from real-frame recognition and live input evidence.

## 2026-11-14 Expanded Reference Candidate Review

The two local reference checkouts were rechecked at AALC `2fcb1b4620108c9bb0cf138f82790dd13f46356c` (`main`, clean) and LALC `431b432e22f0b0da08b95d7c478fa213be20b3e8` (`master`, clean). The raster-path inventory used `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, and `.gif`: 650 paths in AALC and 761 in LALC. Neither checkout has raster files under `tests/`.

Visual review covered every file in these selected groups, using contact sheets and individual inspection of tutorial candidates: AALC's 333 paths under components containing `mirror` and all 12 files under `assets/doc/image`; LALC's 93 Mirror paths, reduced to 90 unique file contents by SHA-256, and 581 unique documentation images across `img/`, `doc/img/`, and `lalc_frontend/assets/doc/img/`. The 22 unique documentation images at least 1280 x 720 were visually reviewed. These groups are a complete review of the stated scopes, not a pixel-level review of every raster in both repositories.

All reviewed AALC and LALC Mirror resources are recognition templates, labels, icons, or crops rather than standalone full-frame gameplay captures. The LALC documentation composites below contain useful Mirror state leads, including screenshots that appear to show broad in-game panels. They are scaled within tutorial layouts and include tutorial text or annotations; their source capture, original dimensions, game version, language, privacy status, and redistribution rights are not established. Treat each as a lead for locating or manually confirming an original, not as a fixture. No image was copied.

| LALC candidate path | Visible Mirror material | Disposition |
| --- | --- | --- |
| `img/tutorial_1_01.png` | Mirror entry and dungeon-selection panels, alongside unrelated game panels. | Tutorial composite; original capture and provenance unknown. |
| `img/tutorial_1_03.png` | Team selection and selection-dialog panels. | Tutorial composite; not a standalone full frame. |
| `img/tutorial_1_05.png` | Theme-pack, shop, and EGO gift-selection panels. | Tutorial composite; embedded shop panel is a useful lead, but native resolution and source are unknown. |
| `img/tutorial_1_06.png` | Shop gift-fusion panel. | Tutorial composite; not a standalone full frame. |
| `img/tutorial_1_07.png` | Team builder, shop, and gift-selection panels. | Tutorial composite with annotations; not a standalone full frame. |
| `img/tutorial_1_08.png` | Theme-pack cards and related configuration material. | Reference artwork/configuration, not a gameplay-state capture. |

The earlier statement that no reviewed item qualifies as a complete labeled frame still holds, but the review is now broader: these tutorial composites are known candidate leads rather than uninspected possibilities. Before any use, locate an original or obtain a newly authorized capture, verify item-specific rights and privacy, and record game version, language, native resolution, scale, UI state, and expected detections. If no lead can be qualified, continue with a small authorized full-frame baseline; do not infer visual coverage from the composites or the existing recognition templates. Temporary contact sheets and manifests were kept outside the repository at `E:\\PUBLIC\\Project\\AALC\\.codex_reference_image_review_2026_11_14`; they are review aids, not project fixtures.

### V1 Source Record and Disposition (2026-11-14)

The local LALC checkout is `E:\PUBLIC\Project\AALC\Source Code\LixAssistantLimbusCompany`, clean at `431b432e22f0b0da08b95d7c478fa213be20b3e8`, with local `origin` recorded as `https://github.com/HSLix/LixAssistantLimbusCompany.git`. `doc/tutorial.md` places the five images below in the task and team-configuration tutorial sections. Git history shows each canonical `img/` file was first added by commit `0d7c6bd1b116846ca2fd530a3e76913951699752`, authored by 陆爻齐-LuYaoQi on 2025-12-31, subject `feat: 重构整个应用 | Rebuild the whole application`. Each stored file is 2000 x 1125 pixels. Matching files under `doc/img/` and `lalc_frontend/assets/doc/img/` are byte-identical duplicates of the canonical `img/` file.

| Canonical LALC path | SHA-256 | Disposition |
| --- | --- | --- |
| `img/tutorial_1_01.png` | `6C87BCE122470968B2CCA9243BCFF424D2E63E7EA804F0F62AEABED3515B6528` | Reject as fixture: tutorial composite with unrelated game panels; retain path as a lead to the original capture. |
| `img/tutorial_1_03.png` | `B3A7A55C53A7A8C61691458118192A0B19B16CA2C2B2A1E8E61CCFB72CE1E586` | Reject as fixture: tutorial composite with multiple panels; retain path as a lead. |
| `img/tutorial_1_05.png` | `C311D2F18073F5298659C0A46BF9FA7498A9A82B5ECA6E2BD4975EC64471515A` | Reject as fixture: tutorial composite with theme, shop and gift panels; retain path as a lead. |
| `img/tutorial_1_06.png` | `D67BCC8A08328DA3BE9AC0F9CDD638D0FB8290A278B77C74DA8BC01B282D8C8E` | Reject as fixture: tutorial composite, not a standalone gameplay frame; retain path as a lead. |
| `img/tutorial_1_07.png` | `F174501CBCCE3131E4B8646F61BB59310B6AA3C646A104D4ECA9751ABAD8634A` | Reject as fixture: annotated tutorial composite; retain path as a lead. |

This completes disposition of the five currently identified tutorial leads: none is accepted as a visual fixture. The Git record identifies when and where these composite files entered the local reference repository; it does not identify the original game capture, game version, language, privacy review, or permission for the embedded game imagery. The repository-level AGPL-3.0 license and its README disclaimer about software icons do not establish rights for these screenshots. No image was copied. V2 therefore still requires a separately authorized full-frame capture or a newly located original with sufficient provenance and permission. Reopen V1 if another candidate is proposed.

### V1 Reopened: Architecture-Refactor Knowledge Images (2026-11-14)

Read-only history review found an additional candidate set on the local cached `refs/remotes/origin/architecture-refactor` ref at `0d480f0093da7d7eeff4510d3063685b041724c7`. This ref is not the clean `master` reference used for the earlier inventory. Commit `6521364566cedc898996aabbaa4c6df533167d53`, authored by HSLix on 2026-11-12 with subject `feat: add the part cursor before capture screenshot;fix: improve the skills`, added the `limbuscompany-knowledge` skill and all images below. The skill describes these as page references and says game updates can make them stale; it provides no per-image capture record, game version, privacy review, or image-rights statement.

A contact sheet was followed by individual native-size viewing of all 17 page images. Each shows a complete 1280 x 720 game interface rather than a tutorial-page collage. All 18 extracted PNGs matched their Git tree blob IDs at the reviewed branch HEAD; this binds the review copies to that commit but cannot establish whether the committed pixels preserve an original capture. Three event images contain `REC`, a timer and crosshair-style marks; local repository evidence does not establish whether these are in-game UI or capture overlays. Privacy and item-specific rights were not qualified. The 190 x 406 `mirror-legend.png` is a cropped legend, not a full-frame candidate. Extracted review files and the contact sheet are under `E:\PUBLIC\Project\AALC\.codex_reference_architecture_ref_2026_11_14`; no image was copied into the AALC repository or used in tests.

Pillow metadata inspection of all 18 PNGs found the same `Software=Snipaste` and `dpi=(167.9956, 167.9956)` fields and no EXIF fields. This is consistent with Snipaste screenshot processing, but supplies no capture timestamp, game version, capture operator, original-resolution history, privacy decision, or reuse permission. It does not establish that the pixels were not edited before commit.

| Candidate path in branch | SHA-256 | Contact-sheet observation |
| --- | --- | --- |
| `src/lalc/skills/limbuscompany-knowledge/mirror-enhance-ego-gift-page.png` | `0A31A94774B3459AC2F8EC7A31E2382FABEBE02D9A04BE1433F9AB558DAC0E8F` | Enhance gift screen. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-entry-page.png` | `2F4E5D952600A8EDDE72B2153F4122619E998D7D8BB418C4F07D85431CAB938C` | Mirror entry screen. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-event-check-page.png` | `20E3C669CEBCF0DF90D764A53DAA469C7AD9289F89583E69313225F40A11123A` | Event check screen. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-event-choices-page.png` | `32BC00BD63C35757062D50A6330817F0541EEAE6C454FCCAFC351B4B0A83BBFF` | Event choice screen. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-event-page.png` | `2E5DBD964E636C3127877F7E5685D2B0E9B7FC883D8E8D5C265697E3880C8BDB` | Event narrative screen; contains visible camera-like marks whose origin is unknown. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-fuse-ego-gift-keywords-page.png` | `42A8DA944B0F4545FFB67C32E36614CCB356BDFF76EA0ED3E0A59F203073F3E8` | Fusion keyword selection. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-fuse-ego-gift-page.png` | `9D54FA63B5BC5B01F15020877A083D8E6FD280A08A6CFB3CA0077CCA0345659E` | Gift fusion screen. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-heal-sinner-page.png` | `E58D16A1FC3A66DCA033D6FF7119CBFACAD8CD80939E774D422ADFE3E3B4D35E` | Heal sinner shop action. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-path-page.png` | `DE597C94DA231BB1F2126A39A6C83EC02582EE26F07CC61EE822B2A944D1BD48` | Mirror route map. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-replace-skill-page.png` | `3E580588E7F23947A1A9C83EE8BCE313261FD36F2575CFAFE4D85904E16BD3ED` | Replace skill shop action. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-search-ego-gift-page.png` | `775080D588BDC535F61956AF76741CA8A54BFA8FBE092E44076BB3E115FAFA5E` | EGO gift search. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-select-ego-gift-page.png` | `BD0066A6D2478C92E88D1708E2B3C056BB2FCD26234F7DDAF59743AC2D6C8217` | Initial EGO gift selection. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-sell-ego-gift-page.png` | `35D58F94B578CDBFD2AD8C19E40F1B996EFF076FF1D3F5BFE1DB7261B5F9088A` | Sell gift shop action. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-shop-page.png` | `7BF4F66619559C275D3606D5362B4568BF9AA4ED5C984B7D7A248C06759B73BC` | Shop screen. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-sinners-page.png` | `1BB8CA3FE58B08DAC27A0A584F912684C605444DA94B04495104B8F50E59E776` | Mirror team selection. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-star-page.png` | `17A398948415AC0ADA403F29A997C76FEA873DD8764EFB443F1D587279A0DAA6` | Star-upgrade selection. |
| `src/lalc/skills/limbuscompany-knowledge/mirror-theme-pack-page.png` | `936D4B90F3766BAE52B952C1658E917CBD07A42731883958BDE2E46BEF19130B` | Theme pack selection. |

Companion exclusion: `src/lalc/skills/limbuscompany-knowledge/mirror-legend.png` is 190 x 406, SHA-256 `4D1366B5B34C34B10CD4230B16501B2FDF2A5333F99687787B8460C51DF924AE`; it is a legend crop, not a full-frame candidate.

**Current disposition:** reopen V1 for the 17 page images. Their Git path, branch, introducing commit, stored dimensions and committed byte identities are known; their original capture context, game version, language, privacy status, pre-commit pixel integrity and item-specific rights are not. The branch and commit attribution is not permission to reuse the embedded game imagery. Do not use these files as fixtures until each candidate passes provenance, privacy and rights review. V2 remains blocked on an authorized full-frame set or qualifying originals.

### Pinned Public-source Follow-up (2026-11-14)

The public GitHub API record for [commit `6521364566cedc898996aabbaa4c6df533167d53`](https://github.com/HSLix/LixAssistantLimbusCompany/commit/6521364566cedc898996aabbaa4c6df533167d53) matches the local commit identity: author and committer `HSLix`, date 2026-11-12 08:03:01 UTC, subject `feat: add the part cursor before capture screenshot;fix: improve the skills`. GitHub reports the commit as unsigned. Its changed-file listing includes the `limbuscompany-knowledge` skill and the Mirror page images; that is repository-history evidence, not original capture provenance.

The pinned [`SKILL.md`](https://github.com/HSLix/LixAssistantLimbusCompany/blob/6521364566cedc898996aabbaa4c6df533167d53/src/lalc/skills/limbuscompany-knowledge/SKILL.md) warns that game updates may change screens, resources or rules and that the knowledge may not match the actual game. It does not record per-image capture date, game version, language, operator, pre-commit edit history, privacy review or reuse permission. This read-only check therefore adds no basis to accept any candidate as a fixture; other records or direct permission may still change an item's disposition. No author was contacted, no image was copied, and no candidate was used in tests.

Additional public-record checks on the same repository found no associated pull request for the commit, zero commit comments, and zero issues matching the exact `limbuscompany-knowledge` term with `is:issue` ([query](https://api.github.com/search/issues?q=repo%3AHSLix%2FLixAssistantLimbusCompany+%22limbuscompany-knowledge%22+is%3Aissue)). These scoped results do not cover external or private discussions, unindexed records, or direct permission. They do not change the pending V1 disposition.

### Publisher Terms Check (2026-11-14)

The current official [Limbus Company Terms of Service](https://limbuscompany.com/terms-of-service/) page states an effective date of 2023-02-27. Article 16 assigns rights in service content to Project Moon and restricts use outside its stated permissions; Article 16.2 says members may not use service information commercially or make it available to others through acts such as copying, reproduction, distribution, display, or transmission without prior consent. The official [2025-09-26 notice](https://store.steampowered.com/news/app/1973530/view/525355229451911687) reports unauthorized sharing of game resources and says the Fanwork Guidelines would be updated. That notice does not itself grant permission to include screenshots in a public code repository. A scoped search of these official terms and Limbus Company announcements located no specific grant for this repository's fixture use; that search does not prove a separate permission or later policy cannot exist.

**Assessment and disposition:** the user-selected preference to save, share, and commit suitable samples records the project direction, but does not establish rights to third-party game content. The 17 branch images remain unqualified for local visual tests and are not accepted for inclusion or distribution in the public AALC repository. Their source attribution and `Software=Snipaste` metadata do not establish original capture context, pixel integrity, privacy status, or permission. No image was copied. Reopen a candidate only when there is an applicable official license/policy or rights-holder authorization covering the intended test use and repository distribution, plus item-specific provenance, integrity, privacy, game version, and language. This is a project risk disposition, not a legal determination.
