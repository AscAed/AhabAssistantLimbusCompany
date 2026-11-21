from pathlib import Path

import pytest
from PIL import Image

from module.automation.automation import Automation, GameState, PageStateDispatcher
from module.config import cfg
from tasks.daily.get_prize import _has_meaningful_mission_list_change
from utils.path_manager import path_manager

_FIXTURE_DIR = Path(__file__).resolve().parents[3] / "fixtures" / "visual"


def _load_visual_fixture(filename):
    fixture_path = _FIXTURE_DIR / filename
    if not fixture_path.is_file():
        pytest.skip(
            f"Visual fixture {filename} is absent from this checkout; "
            "this image-based regression assertion requires the optional fixture"
        )
    with Image.open(fixture_path) as frame:
        return frame.convert("L")


@pytest.fixture
def visual_automation(monkeypatch):
    monkeypatch.setattr(cfg, "set_win_size", 1440)
    monkeypatch.setattr(path_manager, "active_paths", ["default/share", "default/zh_cn"])
    monkeypatch.setattr(path_manager, "current_theme", "default")
    monkeypatch.setattr(path_manager, "current_language", "zh_cn")

    def load_frame(filename):
        screenshot = _load_visual_fixture(filename)

        auto = object.__new__(Automation)
        auto.model = "clam"
        auto.screenshot = screenshot
        auto.screenshot_np = None
        auto.last_screenshot_time = 0
        auto.last_memory_check_time = 0
        auto.memory_protection = False
        auto.img_cache = {}
        auto.location_cache = {}
        return auto

    return load_frame


def test_missing_visual_fixture_is_reported_as_skip(monkeypatch, tmp_path):
    monkeypatch.setitem(
        _load_visual_fixture.__globals__, "_FIXTURE_DIR", tmp_path / "missing"
    )

    with pytest.raises(
        pytest.skip.Exception, match="is absent from this checkout"
    ):
        _load_visual_fixture("mirror-route_choices.png")


@pytest.mark.parametrize(
    ("filename", "expected_state"),
    [
        ("mirror-team_normal.png", GameState.MIRROR_TEAM_SELECT),
        ("mirror-theme-pack_normal.png", GameState.THEME_PACK),
        ("mirror-theme-pack_hard.png", GameState.THEME_PACK),
        ("mirror-shop_normal.png", GameState.SHOP),
        ("mirror-shop-fusion_ready.png", GameState.SHOP),
        ("mirror-route_choices.png", GameState.ROAD_MAP),
    ],
)
def test_dispatcher_recognizes_mirror_visual_fixtures(
    visual_automation, filename, expected_state
):
    auto = visual_automation(filename)

    assert PageStateDispatcher(auto).detect_state() == expected_state


def test_initial_ego_workflow_anchors_match_visual_fixture(visual_automation):
    auto = visual_automation("mirror-ego_initial.png")
    expected_regions = {
        "mirror/road_to_mir/activate_gift_search_off_assets.png": (2000, 0, 2560, 500),
        "mirror/road_to_mir/burn_gift_assets.png": (0, 0, 1000, 600),
        "mirror/road_to_mir/select_init_gift/burn_ego_gift_1.png": (1300, 350, 2200, 650),
        "mirror/road_to_mir/select_init_gift/burn_ego_gift_2.png": (1300, 650, 2200, 850),
        "mirror/road_to_mir/select_init_gift/burn_ego_gift_3.png": (1300, 850, 2200, 1150),
    }

    for target, (left, top, right, bottom) in expected_regions.items():
        position = auto.find_element(target, take_screenshot=False)
        assert position is not None, target
        assert left <= position[0] <= right, (target, position)
        assert top <= position[1] <= bottom, (target, position)


@pytest.mark.parametrize("filename", ["pass-daily_loaded.png", "pass-weekly_loaded.png"])
def test_pass_coin_matches_include_rows_without_proven_claimability(
    visual_automation, filename
):
    auto = visual_automation(filename)
    matches = auto.find_element(
        "pass/pass_coin.png",
        find_type="image_with_multiple_targets",
        take_screenshot=False,
    )

    assert len(matches) == 5
    assert (734, 623) in matches
    assert (734, 798) in matches


def test_daily_and_weekly_fixtures_change_the_mission_list_region(visual_automation):
    daily = visual_automation("pass-daily_loaded.png").screenshot
    weekly = visual_automation("pass-weekly_loaded.png").screenshot

    assert _has_meaningful_mission_list_change(daily, weekly) is True
    assert _has_meaningful_mission_list_change(daily, daily) is False
    assert _has_meaningful_mission_list_change(weekly, weekly) is False
