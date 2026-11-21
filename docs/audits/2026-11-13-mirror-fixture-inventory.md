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

## 2026-11-16 Current Collection Status and Gaps

This is a documentation cross-check against the `cc9e3724` AALC checkout and the local reference refs recorded above. It does not repeat the native-size image review or copy any asset. The LALC main checkout remains `431b432e22f0b0da08b95d7c478fa213be20b3e8`; its cached `origin/architecture-refactor` ref is `952476cfcd231bd9143cee5766ce2161fb306f89`. The 17 full-frame 1280 x 720 Mirror screens remain candidate leads only. Their original capture context, game version, language, privacy disposition, original-pixel integrity and item-specific permission for test use/repository distribution are unverified. Do not include them in local visual tests or the public repository until those conditions are documented. The five LALC tutorial composites, localized labels, runtime crops/templates and legend remain unsuitable substitutes for complete labeled frames.

The user permits samples to be saved, shared and included in the repository. This records project intent; it does not clear rights to embedded game content or resolve provenance. For candidates from a reference project, obtain an applicable policy/license or rights-holder authorization covering the intended test use and distribution, and record evidence per item. If that cannot be established, keep the candidate excluded and seek permission for a suitable source or a newly captured sample under an applicable use basis. User-provided images in conversation are not repository fixtures unless the actual files and their metadata/permission are separately reviewed. The earlier Daily/Weekly pass screenshots informed code discussion but were not retained; the pass-page sample requirement therefore remains open.

| Workflow/state group | Human collection or confirmation needed | System-assisted capture after authorization | Current status |
| --- | --- | --- | --- |
| Team selection | Reach and confirm normal, missing-anchor, selected-team and failure states; label intended team and anchors. | Capture complete frames and metadata during an authorized session after the human confirms the visible state and target labels. | No qualifying full-frame fixture recorded. |
| Initial/observed EGO | Confirm normal, no-match, confusable-gift and final-scroll states and which gift should be selected. | Capture ordered frames and annotate target/no-match regions after state confirmation. | Reference images offer leads, not accepted fixtures; recognition remains unqualified. |
| Shop/fusion | Reach normal, empty, selected, missing-row-anchor, confirmation and failed-transition states; identify expected safe outcome. | Capture each confirmed state with candidate gifts, anchors and expected detection labels. | Runtime resources are crops/templates; no accepted full-frame samples. |
| Route/event | Confirm similar-looking route nodes, route choices and event transitions with expected selection labels. | Capture full frames and annotate route/event targets and no-match cases. | 17 LALC screens include route/event leads but remain rights/provenance blocked. |
| Scroll/layout | Human confirms first/middle/last/no-further-scroll positions and the supported resolution/scale. | Capture ordered frames with position, window size, display scale and language metadata. | Static frames can validate recognition/coordinates only, not actual drag distance or scroll effect. |
| Failure/recovery | Reproduce or deliberately reach the failure state and confirm the desired terminal/recovery outcome; do not fabricate failure labels from normal screenshots. | Capture the visible state and diagnostic context in an authorized session; avoid saving unrelated personal data. | No accepted representative failure-state set. |
| Pass Daily/Weekly | Provide/reconfirm full-frame current pages and expected loaded/no-claim behavior; avoid retaining identifiers. | Capture after the person confirms the selected tab and mission-list state. | Prior conversational samples were not persisted; current synthetic tests are not image fixtures. |

Before any collection, preserve full-frame pixels for tested regions: do not cover or blur targets used for recognition acceptance. If privacy redaction must touch a tested region, mark that region ineligible and do not use it to claim accuracy. Keep a manifest with per-image source, permission basis, capture date/context, game version, language, dimensions, display/window scale, UI state, privacy disposition, SHA-256 and expected labels. A human must confirm state/labels; batch capture or annotation can then be system-assisted. No game session or automated capture was run for this update.

## 2026-11-16 Human Sample Request Checklist

This section is the practical collection request prepared before the latest user-provided images arrived. At that time, the repository had no full-frame raster fixtures under `tests/`; runtime templates/crops and LALC reference images were not substitutes. The user has since added candidate frames under `tests/fixtures/visual/`; their current inventory and review status are recorded below. The proposed categorized layout remains a future organization option; no supplied image was moved or renamed.

### Where to Save

For images you are preparing to send for review, keep the originals outside the Git repository until each file's source, privacy, integrity and intended-use basis have been recorded. A suggested intake folder is `E:\PUBLIC\Project\AALC\_mirror-sample-intake\` with `mirror\` and `pass\` subfolders; this folder is proposed and was not created. After acceptance, use this proposed repository layout:

```text
tests/fixtures/visual/
  README.md
  manifest.yaml
  mirror/
    team/
    ego/
    theme-pack/
    shop-fusion/
    route-event/
    scroll/
    failure-recovery/
  pass/
    daily/
    weekly/
```

The folder names are proposed; no files should be moved or committed by following this checklist alone. Keep one unaltered full-frame PNG per capture. Do not crop, scale, annotate, or overwrite the original. Put any explanatory target boxes in the manifest or a separate review copy, never over the pixels used for recognition acceptance.

Use this filename pattern (ASCII, lowercase, no spaces):

```text
YYYYMMDD_<area>_<state>_<lang>_<width>x<height>_scale-<percent>_game-<version>_<sequence>.png
```

Examples (replace placeholders with the actual values; do not guess a game version):

```text
20261116_mirror-team_normal_zh-cn_1920x1080_scale-100_game-unknown_01.png
20261116_mirror-shop-fusion_no-anchor_zh-cn_1920x1080_scale-100_game-unknown_01.png
20261116_pass-daily_claimable_zh-cn_1920x1080_scale-100_game-unknown_01.png
```

For example, an unreviewed Mirror team capture would first be placed at `E:\PUBLIC\Project\AALC\_mirror-sample-intake\mirror\20261116_mirror-team_normal_zh-cn_1920x1080_scale-100_game-unknown_01.png`. Only after review should an accepted copy be placed under `E:\PUBLIC\Project\AALC\AhabAssistantLimbusCompany\tests\fixtures\visual\mirror\team\` using the same filename.

If the game version is unknown, use `game-unknown` and record why in the manifest. “Scale” means the Windows display scaling used for the capture; also record the game window/client size if it is not full-screen.

For every image, include a manifest entry with: filename; state and whether it is before/after an action; expected visible targets and expected no-match result; game version/build (or unknown); language; pixel dimensions; Windows display scale and game window/client size; capture date and whether manually captured or system-assisted; source/permission basis and intended scope (private review, local tests, repository distribution); any redaction and the exact affected region; and SHA-256 if readily available. Do not include account names, IDs, chat overlays, desktop notifications or unrelated personal data.

### Priority 0: Small Baseline

Please start with one full-frame image for each row below where the state is naturally available. If a state is not available, mark it “not captured”; do not manufacture it by editing another screenshot. These eight images establish an initial visual baseline, not broad accuracy coverage.

| ID | Suggested filename stem | What the full screen should show | Label to provide | Collection |
| --- | --- | --- | --- | --- |
| M-01 | `mirror-team_normal` | Mirror team-formation page with the selected sinners/slots visible and the control used to continue into Mirror visible. Include surrounding UI, not just the team grid. | Which team/slots are valid and the intended continue control. | Human confirms the screen and labels; manual screenshot is sufficient. |
| M-02 | `mirror-ego_initial` | Initial EGO gift-selection page with all visible gift cards and the selection/continue controls. | Intended gift if there is a preferred match; otherwise expected no-match/leave-unchanged result. | Human confirms target; manual screenshot. |
| M-03 | `mirror-theme-pack_normal` | Theme-pack/difficulty selection page with the available choices and current selection visible. | Expected pack/difficulty choice or expected no-match. | Human confirms labels; manual screenshot. |
| M-04 | `mirror-shop_normal` | Shop screen showing the gift grid, visible row boundaries/anchors and shop action controls. | Which gifts and row anchors the current recognition is expected to find. | Human confirms labels; manual screenshot. |
| M-05 | `mirror-shop-fusion_ready` | Fusion screen with candidate gifts arranged in the normal usable layout and the relevant fuse/confirm control visible. | Candidate gift locations, row anchor and expected selection outcome. | Human confirms labels; manual screenshot. |
| M-06 | `mirror-route_choices` | Route map with multiple visible nodes, including at least two visually similar choices if naturally present. | Intended node and labels for the other visible node types. | Human confirms route state/targets; manual screenshot. |
| P-01 | `pass-daily_loaded` | Daily pass mission-list page after the list has finished loading, with the tab and mission rows visible. | Confirm selected Daily tab and whether the page is loaded; do not infer claimability from coin artwork alone. | Human confirms state; manual screenshot. |
| P-02 | `pass-weekly_loaded` | Weekly pass mission-list page after loading, with tab and mission rows visible. | Confirm selected Weekly tab, loaded state and visible mission progress. | Human confirms state; manual screenshot. |

If only a minimal upload is practical, prioritize M-01 through M-06 and the two pass pages above. For pass pages, a loaded screen alone does not establish the claim/no-claim behavior; the follow-up states below are needed before qualifying those branches.

### Priority 1: High-Risk and Easily Confused States

Collect these after the baseline, when the state can be reached without risking account or user data. These are separate images, not edits of the baseline.

| ID | Suggested filename stem | What is missing and what to capture | Label to provide | Collection |
| --- | --- | --- | --- | --- |
| M-07 | `mirror-team_missing-anchor` | Team page where the expected row/anchor is absent or visually different, if this can occur naturally. | Which anchor is absent and the expected safe outcome (no selection/stop). | Human must confirm the actual state; system-assisted capture may save the full frame after confirmation. |
| M-08 | `mirror-ego_confusable` | Gift choices with similar artwork/text or a target partly near the edge. | Correct target, confusing alternatives and expected no-match if the target cannot be distinguished. | Human confirms labels; capture may be system-assisted. |
| M-09 | `mirror-ego_last-scroll` | Last visible gift row after scrolling, including the end-of-list boundary. | Visible gifts, intended target if any, and whether more scrolling is expected. | Capture an ordered set; system-assisted capture is useful once a human confirms each position. |
| M-10 | `mirror-shop-fusion_missing-anchor` | Fusion/shop state where the row anchor or expected reference is absent; do not edit a normal image to simulate absence. | Missing anchor and expected fail-closed result. | Only collect if naturally reachable; otherwise keep the visual case blocked and use a separately labeled synthetic test for control flow. |
| M-11 | `mirror-shop-fusion_after-selection` | Screen after selecting one or more fusion gifts, before final confirmation, with selected state visible. | Which gifts are selected and which next action is expected. | Human confirms action/state; system-assisted sequence capture can preserve before/after ordering. |
| M-12 | `mirror-shop-fusion_result` | Result page after a completed fusion, if available. | Expected result marker and return/continue control. | Human confirms result; system-assisted capture may record the transition. |
| M-13 | `mirror-route_event_choice` | Event-choice page with the choices fully visible, preferably including one misleading/similar choice. | Intended choice and alternatives; mark any unknown/no-match case. | Human confirms event text/choice; manual or authorized system-assisted capture. |
| M-14 | `mirror-route_transition` | Route/event transition page after an action, not just a static route map. | Before/after state and expected next page. | Ordered capture after human confirmation; a static image cannot prove the transition occurred. |
| M-15 | `mirror-scroll_first` / `mirror-scroll_middle` / `mirror-scroll_last` | Three full frames of the same scrollable page at the top, middle and end; capture them in order without changing scale or window size. | Order, visible item identities and whether the end has been reached. | Best captured as an authorized sequence; manual images are acceptable if the order is recorded. These do not alone verify drag distance. |
| P-03 | `pass-daily_claimable` | Daily page with a reward that the UI actually presents as claimable and the relevant row/control visible. | Which row is claimable and the visible evidence for that state. | Human must confirm claimability from the actual UI; do not use the coin icon alone as proof. |
| P-04 | `pass-daily_no-claim` | Daily page with no currently claimable reward, or all visible eligible rewards already claimed. | Why no claim should occur and expected no-op result. | Human confirms progress/claimed state; manual screenshot. |
| P-05 | `pass-weekly_claimable` | Weekly equivalent of P-03. | Claimable row and its visible state. | Human confirms; manual screenshot. |
| P-06 | `pass-weekly_no-claim` | Weekly equivalent of P-04. | Expected no-op and why. | Human confirms; manual screenshot. |
| R-01 | `mirror_failure_loading` | A genuine loading/wait state that can be captured without interrupting or damaging the session. | What is still loading and the safe expected behavior (wait, timeout or stop). | Do not deliberately force a failure; system-assisted capture only in an authorized session. |
| R-02 | `mirror_failure_no-match` | A genuine unsupported/unknown page or no-match state, if encountered. | Expected no-click/stop result and why the state is unknown. | Human identifies the state; otherwise use a synthetic fixture labeled synthetic, not as live visual evidence. |

### Human-Provided Versus System-Assisted Work

- **Needs human capture or confirmation:** confirm that the screenshot really shows the named game state; identify the intended team, card, route node or reward row; confirm Daily/Weekly tab and claimability; state the game version/language if known; confirm the source and permission scope; review privacy/redactions. A script cannot infer these labels reliably from the filename.
- **Can be system-assisted after confirmation:** save full frames in a consistent format; capture before/after or first/middle/last sequences; record timestamps and dimensions; compute hashes; batch-annotate target boxes in a sidecar manifest. Capture must use an authorized game session and must not click, navigate or collect data as part of this sample request.
- **Do not collect by intentionally causing:** account/network failures, data loss, updater interruption, or other damaging states. For rare failures, use labeled synthetic images for control-flow tests and keep them distinct from real-game visual samples.

### Permissions and Current Candidate Status

Your “批准授权” confirms that you are willing for suitable samples to be received, saved and considered for project tests/repository inclusion. It is not recorded as a rights-holder grant for third-party game artwork. For the 17 LALC reference frames, the local repository history identifies candidate files but not original capture provenance or an applicable item-specific permission for local testing and repository distribution; they remain excluded unless that evidence is supplied. The easiest path is to provide new full-frame captures with their own source/context and permission scope, then review them one by one. A user-provided image is still pending review until its file, tested-region integrity, privacy and intended distribution scope are checked.

No images were requested from, extracted from, or copied out of the reference repositories in this update. No game, application, build, updater or capture process was run.

## 2026-11-16 User-supplied Frame Review

The user reported adding eight full-frame images under `tests/fixtures/visual/`. A read-only directory listing found **nine** PNG files. All nine decode as **2560 x 1440**; SHA-256 values below bind this review to the exact files inspected. The extra file is the Hard theme-pack page. Visual inspection found complete 16:9 game screens with the named workflow visible. Several images show a `CUSTOM LANGUAGE` footer; its source and effect on the tested UI are not established. The initial visual spot check found no obvious account identifier or desktop notification; the later full-frame and metadata privacy screen is recorded under `User Screenshot Privacy Screen (2026-11-16)`.

| File | SHA-256 | Observed screen and disposition |
| --- | --- | --- |
| `mirror-team_normal.png` | `4D2E4DA7E5CEA74195BD23EDC41CD8C68825AE34DF041474C1CD8235998F1BB7` | Full team/preset screen, roster and confirmation control visible. User-defined behavior: identify the team by its order in the left-side formation list, verify it, then click the bottom-right confirmation control. |
| `mirror-ego_initial.png` | `8B00B916C5FFF3D2D42970F0E2900A626F03D3B613BA65DAC45B9CD7B5640A29` | Full initial EGO decoration/gift-selection page. User-defined behavior: choose the configured category on the left, then select the configured number and order from the three gifts on the right; selection order may be non-contiguous. Apply the observation toggle according to configured observation gifts. |
| `mirror-theme-pack_normal.png` | `EDFDAB76D78AED2EED5896199F655216EC30A478ED7C710C24C59FFD98EAA169` | Full Normal theme-pack selection page. Expected selection is derived from the Normal priority configuration for the selected team/floor. |
| `mirror-theme-pack_hard.png` | `0ACC8D03CDC0D020168843813BEAEBA638EF30358DC7A85189DA7B84130E805F` | Full Hard theme-pack selection page; additional coverage beyond the original eight requested frames. Expected selection is derived from the Hard priority configuration for the selected team/floor. |
| `mirror-shop_normal.png` | `1BFF05D84DC8047E05C40A814AC3776D35DE09DE3E0CDC4744DC1E1464AAED86` | Full shop screen with gift grid and shop controls. The user confirmed the black bars are original screen content and do not obscure item names or prices; treat those visible rows as usable candidates. |
| `mirror-shop-fusion_ready.png` | `BB20F229855B62E9DC3A412BA2A639F96D20823689EFB78A1FE9FFAAB8371A9E` | Full fusion overlay with candidate gifts and fusion controls, but formula slots are empty and the screen says to select keywords. User-defined next action: click the left fusion area to open keyword selection, then choose configured fusion categories. The file depicts the pre-keyword state; filename is preserved. |
| `mirror-route_choices.png` | `60A50A9156803ECC2A96914E9631A794EF78636CDC3EE2A6D318445EA261C827` | Full route map with multiple route nodes and current position. User-defined behavior: zoom out by mouse wheel until all nodes are visible, plan by node priority, then navigate with directional keys. The current test configuration must explicitly enable keyboard navigation. |
| `pass-daily_loaded.png` | `54A4A2B89C9E33470D8E597EF924555A587DF5A30A3FC4B5E99878A52159B6C5` | Full Daily mission page with selected tab, loaded rows and progress. Supports loaded-page state only; it does not establish a claimable reward or no-claim completion behavior. |
| `pass-weekly_loaded.png` | `E9CA9EA02BF488089726D4EF94618813C7A9518CD0E1D66F2150213B36F4E59F` | Full Weekly mission page with selected tab, loaded rows and progress. Supports loaded-page state only; it does not establish a claimable reward or no-claim completion behavior. |

**Evidence status:** these are user-supplied candidate fixtures and are present as untracked files in the current worktree. Their visual completeness and dimensions are verified; the later persistent tests that reference them are listed under `Persistent Workflow Recognition Regressions (2026-11-16)`. The user reports Season 8/new-season imagery, capture on November 16 using a screenshot tool, a 32-inch 2560x1440 monitor at 100% Windows scale, and full-screen mode. Exact game build/version and screenshot-tool name remain unspecified. The user confirmed that the shop black bars are original content and do not obscure prices or names. The user authorizes public repository inclusion if a recognition workflow needs the screenshots. This records provenance and project-use intent; the applicable rights basis for public distribution of embedded game content remains a separate project review item.

**User-confirmed expected flows and implementation cross-check (2026-11-16):** the project should not ask the user to restate expected pack names or routes when those can be derived from an explicit fixture-test configuration. Current AALC supports selecting teams by order (`select_team_by_order`), choosing configured initial EGO categories/orders, applying the observation-gift toggle, choosing theme packs by Normal/Hard priority configuration, and planning routes from recognized graph nodes. `mirror_keyboard_navigation` is a separate switch and is `False` in the example config; the test config must set it to `True` to assert the user's described keyboard-navigation path. Current fusion flow recognizes the initial keyword prompt and proceeds to keyword selection; the supplied image labels the state before that interaction. The local AALC reference at `2fcb1b4620108c9bb0cf138f82790dd13f46356c` is the closest implementation reference for these Python/config patterns. LALC `431b432e22f0b0da08b95d7c478fa213be20b3e8` also uses config-driven theme/gift decisions, but its Flutter/backend workflow and fixed coordinates are not a drop-in source of AALC coordinates. These are static code/config checks, not visual or live-game validation.

The screen banner reads `2026.09.17 (KST) - until Season 9 begins`, while the user identifies the screenshots as newly captured Season 8 screens on November 16, 2026. The banner is not treated as capture metadata. The unresolved discrepancy is within the banner's stated date/Season 9 meaning, not between the user-provided capture date and Season 8 label.

### 2026-11-17 Official Season-context Recheck

The official [Limbus Company Steam news feed](https://store.steampowered.com/news/posts/?enddate=1788771604&feed=steam_community_announcements) lists `Guide on Season 8: Punctum` dated September 7, 2026. An [independent archive transcription](https://lcna.whosmalikx.com/notices/2026-09-16-guide-on-season-8-punctum/) attributed to Project Moon states that Season 8 commences on September 17, 2026, at 12:00 KST. This establishes the scheduled Season 8 start date, not the screenshot capture date, the current season on November 16, or the screenshots' installed client version. The user's Season 8/capture-date statements remain user-provided metadata. The banner's association of September 17 with Season 9 remains unexplained; do not treat it as capture metadata or proof of a client version.

### 2026-11-16 Offline Page-state Probe

The current full-frame candidates were evaluated locally in a disposable source snapshot based on `cc9e3724876b81be7bbb201c1bb25d2d008c5c57`, with the current `module/automation/automation.py` worktree overlay (`50D6255DD162FC83532F2696366C7768D79A425CFB1631ECAB00B54D8F94D2C0`) and the nine user-supplied PNGs. The probe initialized the image search paths, set the 1440-pixel reference height, preloaded each PNG as the current screenshot, and invoked `PageStateDispatcher.detect_state()`. It did not invoke OCR, task workflows, mouse/keyboard input, the application, or the game.

| Fixture | Result after the current overlay |
| --- | --- |
| `mirror-team_normal.png` | `MIRROR_TEAM_SELECT` |
| `mirror-ego_initial.png` | `UNKNOWN` |
| `mirror-theme-pack_normal.png` | `THEME_PACK` |
| `mirror-theme-pack_hard.png` | `THEME_PACK` |
| `mirror-shop_normal.png` | `SHOP` |
| `mirror-shop-fusion_ready.png` | `SHOP` |
| `mirror-route_choices.png` | `ROAD_MAP` |
| `pass-daily_loaded.png` | `UNKNOWN` |
| `pass-weekly_loaded.png` | `UNKNOWN` |

Before the overlay, the team, route, and both theme-pack frames were recognized, while both shop frames returned `UNKNOWN`. The `shop_coins_assets.png` template scored 0.9935 against the full normal-shop frame but failed when matched inside the dispatcher's default shop ROI: the template's screen-relative bounding box was not translated into cropped-frame coordinates. A synthetic full-size frame reproduced the same failure. The overlay translates the bounding box by the ROI origin before matching. The fusion frame contains `fuse_to_select_keyword_assets.png` at a full-frame match score of 0.9174, but that anchor was not part of the shop state check; it is now included.

Focused tests were run in the isolated snapshot with the three current source/test overlays: `tests/unit/module/automation/test_state_flow.py` and `tests/unit/module/automation/test_vision.py` passed **20 tests** on Python 3.12.13. The new ROI regression synthesizes a frame from the tracked shop-currency runtime template; it does not load the user screenshots. The screenshot result table is a one-off offline characterization, not a persistent test oracle. EGO initial and pass pages remain unclassified by the Mirror dispatcher and need separate workflow/state analysis before adding labels or changing task behavior.

These results establish recognition only for the displayed state labels and current templates. They do not verify target choices, OCR, coordinates for user actions, fusion selection, pass claimability, scrolling, transition timing, or live input. The screenshots remain untracked. Their exact game build, the Season 8/Season 9 banner discrepancy, and a suitable basis for public distribution of game imagery remain open.

### 2026-11-16 Persistent Workflow Recognition Regressions

The user explicitly approved repository inclusion when recognition tests need these screenshots. The current worktree now has `tests/unit/module/automation/test_visual_fixture_recognition.py`, which directly loads all nine PNGs in grayscale to match the application's default screenshot format. Six Mirror frames assert their existing `PageStateDispatcher` labels. The initial EGO frame asserts the configured Burn category, observation-off toggle, and three Burn gift targets in their expected broad screen regions. The Daily and Weekly frames exercise the same `image_with_multiple_targets` matcher used by `get_pass_prize()`.

On both pass frames, the current `pass_coin.png` matcher returns five row-icon locations, including the two visually incomplete mission rows. This confirms the icon is not a claimability signal. The new test records template behavior only; it does not call `get_pass_prize()`, click, OCR, or assert which rewards should be claimed. No behavioral change is made to pass rewards without a representative claimable state and a reliable claimability cue.

The current regression test does not change the one-off state-dispatch results above: initial EGO and Daily/Weekly still return `UNKNOWN` from the Mirror dispatcher because their workflows use dedicated task anchors. The tests validate only page labels and the named target matches. They do not validate live selection, config interpretation, OCR, scrolling, animation, click effects, or real-game transitions. The nine PNGs remain user-provided, uncommitted worktree files; the user has approved their inclusion if required. The exact game build, Season 8/banner-date discrepancy, formal rights basis for game artwork, and complete privacy review remain open and are not inferred from the test pass.

**Still missing for the first visual baseline:** exact game build/version and resolution of the in-game Season 9 banner discrepancy; a fusion frame after the keyword window opens/selection (and ideally a result frame); and Daily/Weekly claimable plus no-claim examples. Scrolling, confusable/no-match and genuine failure/recovery states remain later coverage. The initial visual spot-check did not run game, application, tests, build or capture; the later offline probe and focused tests are recorded above. The supplied frames still do not prove OCR/recognition accuracy, click effects, scrolling, live transitions or application behavior.

### Terms Scope Recheck (2026-11-15)

The current official [Terms of Service](https://limbuscompany.com/terms-of-service/) also contains Article 16-1, which permits qualifying gameplay videos subject to its conditions. It limits use in those videos to non-commercial purposes while separately allowing specified platform advertising and viewer donations. It prohibits unoriginal videos made from game-screen cuts or soundtrack without a specific explanation, bars unauthorized videos from implying Project Moon's endorsement, and requires a specified ownership/disclaimer notice. This is a limited video policy; it does not expressly grant permission to distribute standalone screenshot files as test fixtures in a public source repository. Article 4.7 says Korean is the original language and translations are for reference, so this scope check relies on the English page as a reference. The 2025-09-26 notice said the Fanwork Guidelines would be updated and identified unauthorized sharing of game resources as a concern; a scoped search of official terms and Limbus Company announcements did not surface a later published update. That search is limited and does not establish that no separate permission or later policy exists. The fixture disposition above therefore remains unchanged pending an applicable permission basis and item-specific evidence. This is a project risk assessment, not a legal determination.

### Official Policy Recheck (2026-11-16)

The official [Terms of Service](https://limbuscompany.com/terms-of-service/) page was rechecked on 2026-11-16. It still states an effective date of 2023-02-27. Article 16 assigns rights in company-produced service content to Project Moon and restricts making service information available to others by reproduction or distribution without prior consent. Article 16-1 expressly describes a conditional permission for gameplay videos; it does not expressly address standalone PNG files distributed as public-repository test fixtures. Article 4.6 says country-specific supplementary provisions may apply based on residence and may supersede these terms; the scoped official-site search did not identify a U.S.-specific addendum, so the applicable U.S. terms remain unverified. Article 4.7 says Korean is the original language and the English text is for reference.

The official [2025-09-26 announcement](https://store.steampowered.com/news/app/1973530/view/525355229451911687) says Project Moon planned to update its Fanwork Guidelines and names unauthorized sharing of relevant resources among the concerns. A scoped search of official Limbus Company Terms and Steam announcements did not locate a later published guideline or an explicit grant covering public-repository screenshot fixtures. Search failure does not prove no separate policy or permission exists. Keep the user screenshots untracked and out of public commits until an applicable permission basis is documented. This remains a project risk disposition, not a legal determination.

### User Screenshot Privacy Screen (2026-11-16)

All nine original 2560 x 1440 user-provided frames were reviewed individually at full-frame view for account names or IDs, chat overlays, desktop notifications, and unrelated application windows. None were observed. A read-only Pillow metadata inventory of `tests/fixtures/visual/*.png` found `Image.info` empty and no EXIF items in all nine files. This is a visual-content and embedded-metadata screen; it does not establish pixel-edit history, identify the source of the `CUSTOM LANGUAGE` footer, or determine rights to reproduce game artwork.

**Disposition:** the visible-personal-data screening is complete for these exact nine files as currently present. Keep image hashes as the binding identity and repeat this screen if a file changes. The formal public-distribution basis remains unresolved despite the user's project-use approval; retain the images as untracked local test fixtures and do not publish them until an applicable policy/license or rights-holder authorization is documented. This is a project privacy/risk record, not a legal determination.

### Official Policy Recheck (2026-11-17)

The current official [Terms of Service](https://limbuscompany.com/terms-of-service/) page was rechecked on November 17, 2026. It states that company-produced service content belongs to Project Moon and Article 16.2 restricts reproduction, publication, or distribution to others without prior consent. Article 16-1 expressly permits qualifying gameplay videos under conditions, including restrictions on unoriginal videos made from game-screen cuts without specific explanation; it does not expressly grant permission for standalone PNG screenshots as public-repository test fixtures.

Article 4.6 says country-specific supplementary provisions may apply based on a member's residence and may supersede the main terms. Article 4.7 says Korean is the original language and translations are for reference. The user's applicable residence-based addendum has not been established. A scoped search of official terms and Limbus Company Steam announcements found the 2025-09-26 notice that Fanwork Guidelines would be updated and raised unauthorized sharing of relevant resources as a concern, but did not locate a later published guideline or explicit grant for public-repository screenshot fixtures. Search absence is not proof that no separate policy or permission exists.

**Disposition:** keep the nine screenshots local and untracked. Do not include them in public commits until an applicable permission basis is documented. User capture and project-use intent do not independently resolve redistribution rights. This is a risk assessment, not a legal determination.

### 2026-11-17 Pass List Region Fixture Baseline

The persistent visual regression now loads `pass-daily_loaded.png` and `pass-weekly_loaded.png` as grayscale frames and passes them to the existing `_has_meaningful_mission_list_change()` helper. In the current isolated source copy, Daily-to-Weekly returned `True`; Daily-to-Daily and Weekly-to-Weekly returned `False`. This grounds the existing mission-list ROI threshold against the two available labeled full frames, but the pair is not a temporal capture sequence and does not show that a click caused the difference.

The test module passed **10 tests** and the complete config-free snapshot passed **533 tests, 2 Windows symlink skips of 535 collected**, with Ruff and compileall passing. The regression test SHA-256 is `87BC1D8E129666402BA72D4CB3EBB69D5932E97AC70CD7134D627814201270B9`; the fixture README SHA-256 is `44AB6A68530ED2FADE3E4F8306FE3AE8B73AE46A8BA2C186647B9FD569951635`. The samples remain untracked. This check does not establish transition timing, reward claimability, OCR correctness, or live task behavior.

### 2026-11-17 Claimability Behavior Review

Current source review confirms `get_pass_prize()` clicks every coordinate returned by `auto.find_element("pass/pass_coin.png", find_type="image_with_multiple_targets")` on both the Daily and Weekly pages. The persistent fixture test asserts five matches on each supplied frame, including positions on rows with visible incomplete progress. The two screenshots are static loaded-page examples; neither provides a confirmed completed-but-unclaimed state. Therefore, existing tests establish template presence and mission-list image differences only; they do not establish safe reward selection. Current code attempts clicks on incomplete-row matches, although this offline review cannot establish whether the game accepts or ignores those clicks.

**Implementation gate:** obtain full-frame, manually labeled examples for incomplete, completed-but-claimable, and already-claimed rows. Then compare a state detector against all three groups and assert that only confirmed claimable rows receive input. Also decide the no-claim outcome: return success when the page is verified and no claimable row exists, or fail when claimability cannot be determined. Preserve current behavior only as an explicitly accepted interim policy; do not infer the user's preference from the loaded-page fixtures. No code, screenshots, or game state were changed or collected for this review.

### 2026-11-17 External Pass Candidate Intake Recheck

Read-only inspection of `E:\PUBLIC\Project\AALC\.codex_pass_page_samples_2026-11-15` found exactly two files and no manifest:

| External filename | Bytes | SHA-256 | Pillow format and dimensions |
| --- | ---: | --- | --- |
| `daily_loaded_claimable.png` | 291,446 | `2CC2F77775D9D5B27A081253D1AAE2520274C55B0CCCA21EAEBEB5DDA2345AE8` | JPEG, 1920 x 1080, RGB |
| `weekly_loaded_claimable.png` | 290,699 | `0B0725A15C56570A47F05C405004DD539D04B8A0EDCD94DB04E7FA64734F3EA7` | JPEG, 1920 x 1080, RGB |

Both files have JPEG content despite their `.png` extensions. Pillow reported no EXIF data. Manual full-frame review found visible `CLEAR` rows and incomplete counters: Daily has `0/1`, `0/1`, `0/2`, and `0/10` rows; Weekly has `1/5` and `3/5` rows. Neither image shows a visibly completed-but-unclaimed row. The filenames are not verified state labels and do not make these positive claimability samples.

**Disposition:** retain these candidates outside the repository and do not rename, copy, or use them to calibrate a claimability detector. They may document loaded-page appearance and incomplete rows only; the meaning of the `CLEAR` rows was not independently confirmed. Request full-frame Daily and Weekly examples with a human-confirmed state label, capture context, and manifest before implementing reward selection. The explicit no-claim outcome and applicable screenshot-use/distribution basis remain unresolved. No application, game, source code, fixture, or runtime state was changed during this intake recheck.

### 2026-11-22 User-authorized Fixture Inclusion

The user previously confirmed that the nine full-frame PNGs listed in `User-supplied Frame Review` were captured from their own game session and explicitly authorized public repository inclusion when recognition tests need them. `tests/unit/module/automation/test_visual_fixture_recognition.py` loads those exact files, so the nine PNGs are included under `tests/fixtures/visual/` in this change. The prior statements that they remained untracked describe the state at those earlier audit dates and are superseded for the current checkout.

The recorded capture context, per-file SHA-256 values, 2560 x 1440 dimensions, and privacy screen bind the included files to the reviewed samples. Their pixels were not edited. The user authorization supports this project decision; the prior policy review did not independently establish rights-holder permission for standalone public distribution of game-content images. That rights question remains unverified and is not presented as resolved. These fixtures are test-only and do not qualify live-game behavior or pass reward claimability.
