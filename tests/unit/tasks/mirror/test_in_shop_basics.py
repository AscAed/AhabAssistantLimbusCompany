from unittest.mock import patch

import pytest

from module.config.config_typing import TeamSetting
from tasks import all_systems
from tasks.base.screenshot import wait_for_screenshot as base_wait_for_screenshot
from tasks.mirror.in_shop import Shop, _is_protected_coordinate, wait_for_screenshot


def _patch_two_attempt_screenshot_waiter():
    return patch(
        "tasks.mirror.in_shop.wait_for_screenshot",
        side_effect=lambda: wait_for_screenshot(max_attempts=2),
    )


def test_shop_constructor_builds_sell_list_from_team_setting():
    team = TeamSetting(team_system=0, system_bleed=True, system_charge=True)
    shop = Shop(team)

    assert shop.system == all_systems[0]
    assert "bleed" in shop.shop_sell_list
    assert "charge" in shop.shop_sell_list


def test_shop_constructor_keeps_team_system_out_of_sell_list():
    team = TeamSetting(team_system=0, system_burn=True)
    shop = Shop(team)

    assert all_systems[0] not in shop.shop_sell_list


def test_wait_for_screenshot_retries_until_success():
    with patch("tasks.base.screenshot.auto") as mock_auto:
        expected = object()
        mock_auto.take_screenshot.side_effect = [None, None, expected]

        assert base_wait_for_screenshot() is expected

    assert mock_auto.take_screenshot.call_count == 3


def test_wait_for_screenshot_raises_after_bounded_attempts():
    with patch("tasks.base.screenshot.auto") as mock_auto:
        mock_auto.take_screenshot.return_value = None

        try:
            base_wait_for_screenshot(max_attempts=2)
        except RuntimeError:
            pass
        else:
            raise AssertionError("expected RuntimeError")

    assert mock_auto.take_screenshot.call_count == 2


def test_is_protected_coordinate_honors_scale_and_offset():
    assert _is_protected_coordinate((150, 100), (100, 100), scale=1.0, x_offset=50)
    assert not _is_protected_coordinate((250, 100), (100, 100), scale=1.0, x_offset=50)


def test_processing_coordinates_sorts_dedupes_and_filters_aggressive_rows():
    team = TeamSetting(team_system=0)
    shop = Shop(team)
    shop.fuse_aggressive_switch = True
    shop.the_first_line_position = 200

    points = [(300, 100), (100, 400), (104, 404), (200, 500)]
    with patch("tasks.mirror.in_shop.cfg") as mock_cfg:
        mock_cfg.set_win_size = 1440
        result = shop._processing_coordinates(points)

    assert (100, 400) in result
    assert (104, 404) not in result
    assert (200, 500) in result
    assert (300, 100) not in result


@patch("tasks.mirror.in_shop.retry", return_value=True)
@patch("tasks.mirror.in_shop.sleep", return_value=None)
@patch("tasks.mirror.in_shop.auto")
@patch("tasks.mirror.in_shop.cfg")
def test_standard_fusion_skips_candidates_without_aggressive_row_anchor(
    mock_cfg, mock_auto, mock_sleep, mock_retry
):
    team = TeamSetting(team_system=0, shop_strategy=2, system_charge=True)
    shop = Shop(team)

    def find_element(image_path, *args, **kwargs):
        if image_path == "mirror/shop/enhance_gifts/charge.png":
            return [(100, 100)]
        return None

    mock_cfg.set_win_size = 1440
    mock_auto.take_screenshot.return_value = object()
    mock_auto.find_element.side_effect = find_element

    shop.fuse_useless_gifts()

    mock_auto.mouse_click.assert_not_called()


def test_after_fuse_iv_keeps_aggressive_mode_for_enabled_second_system():
    team = TeamSetting(
        team_system=0,
        shop_strategy=2,
        after_level_IV=True,
        after_level_IV_select=2,
        second_system=True,
        second_system_select=1,
        second_system_action=[1, 0, 0, 0],
    )
    shop = Shop(team)

    assert shop.second_system_action[0] == 1
    assert shop.second_system_action[0] is not True

    shop.after_fuse_IV()

    assert shop.fuse_switch is True
    assert shop.fuse_aggressive_switch is True


@patch("tasks.mirror.in_shop.sleep", return_value=None)
@patch("tasks.mirror.in_shop.wait_for_screenshot", return_value=object())
@patch("tasks.mirror.in_shop.auto")
def test_enter_fuse_selects_enabled_second_system_keyword(
    mock_auto, mock_wait_for_screenshot, mock_sleep
):
    team = TeamSetting(
        team_system=0,
        shop_strategy=2,
        second_system=True,
        second_system_select=1,
        second_system_action=[1, 0, 0, 0],
    )
    shop = Shop(team)
    shop.fuse_IV = True
    mock_auto.click_element.return_value = True

    assert shop.enter_fuse() is True

    mock_auto.click_element.assert_any_call(
        f"mirror/shop/keyword/keyword_{all_systems[1]}.png"
    )
    assert not any(
        call.args[0] == f"mirror/shop/keyword/keyword_{all_systems[0]}.png"
        for call in mock_auto.click_element.call_args_list
    )


@patch("tasks.mirror.in_shop.wait_for_screenshot")
@patch("tasks.mirror.in_shop.auto")
def test_enter_fuse_bounds_repeated_keyword_navigation(mock_auto, mock_wait):
    screenshot_attempts = 0
    target = "mirror/shop/fuse_to_select_keyword_assets.png"

    def wait_for_screenshot():
        nonlocal screenshot_attempts
        screenshot_attempts += 1
        if screenshot_attempts > 16:
            raise AssertionError("enter_fuse exceeded its retry limit")

    mock_wait.side_effect = wait_for_screenshot
    mock_auto.click_element.side_effect = lambda path, **kwargs: path == target
    shop = Shop(TeamSetting(team_system=0))

    assert shop.enter_fuse() is False

    assert screenshot_attempts == 16
    assert sum(call.args[0] == target for call in mock_auto.click_element.call_args_list) == 16


def test_fuse_gift_stops_when_system_fusion_entry_fails():
    shop = Shop(
        TeamSetting(team_system=0, shop_strategy=1, only_system_fuse=True)
    )

    with (
        patch.object(shop, "enter_fuse", return_value=False),
        patch("tasks.mirror.in_shop.auto") as mock_auto,
    ):
        assert shop.fuse_gift() is False

    mock_auto.find_element.assert_not_called()
    mock_auto.mouse_click_blank.assert_not_called()


@patch("tasks.mirror.in_shop.retry", return_value=True)
@patch("tasks.mirror.in_shop.sleep", return_value=None)
@patch("tasks.mirror.in_shop.auto")
@patch("tasks.mirror.in_shop.cfg")
def test_fuse_useless_gifts_no_gifts_returns_cleanly(mock_cfg, mock_auto, mock_sleep, mock_retry):
    mock_cfg.set_win_size = 1440
    mock_auto.take_screenshot.return_value = object()
    mock_auto.find_element.return_value = None

    team = TeamSetting(team_system=0)
    shop = Shop(team)
    shop.fuse_useless_gifts()

    mock_auto.mouse_click_blank.assert_called_once_with(times=3)


def test_aggressive_fusion_stops_when_result_screenshot_wait_fails():
    shop = Shop(TeamSetting(team_system=0))
    original_wait_for_screenshot = wait_for_screenshot
    level_three_matches = 0

    def find_element(image_path, *args, **kwargs):
        nonlocal level_three_matches
        if image_path == "mirror/shop/fuse_label.png":
            return [(100, 100)]
        if image_path == "mirror/road_to_mir/observe_ego_gift/Level_III.png":
            level_three_matches += 1
            return level_three_matches <= 3
        return None

    with (
        patch("tasks.mirror.in_shop.cfg") as mock_cfg,
        patch("tasks.mirror.in_shop.sleep"),
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        patch(
            "tasks.mirror.in_shop.wait_for_screenshot",
            side_effect=lambda: original_wait_for_screenshot(max_attempts=2),
        ) as mock_wait_for_screenshot,
    ):
        mock_cfg.set_win_size = 1440
        mock_auto.find_element.side_effect = find_element
        mock_auto.take_screenshot.side_effect = [object(), None, None]

        with pytest.raises(RuntimeError, match="等待截图超时"):
            shop.fuse_useless_gifts_aggressive()

    mock_wait_for_screenshot.assert_called_once_with()
    assert mock_auto.take_screenshot.call_count == 3
    assert mock_auto.mouse_click.call_count == 3
    mock_auto.click_element.assert_not_called()


def test_aggressive_fusion_stops_after_bounded_no_match_attempts():
    shop = Shop(TeamSetting(team_system=0))
    level_three_matches = 0

    def find_element(image_path, *args, **kwargs):
        nonlocal level_three_matches
        if image_path == "mirror/shop/fuse_label.png":
            return [(100, 100)]
        if image_path == "mirror/road_to_mir/observe_ego_gift/Level_III.png":
            level_three_matches += 1
            return level_three_matches <= 3
        return None

    with (
        patch("tasks.mirror.in_shop.cfg") as mock_cfg,
        patch("tasks.mirror.in_shop.sleep"),
        patch("tasks.mirror.in_shop.retry", return_value=True),
        patch("tasks.mirror.in_shop.auto") as mock_auto,
    ):
        mock_cfg.set_win_size = 1440
        mock_auto.find_element.side_effect = find_element
        mock_auto.take_screenshot.return_value = object()
        mock_auto.click_element.return_value = False

        shop.fuse_useless_gifts_aggressive()

    assert mock_auto.take_screenshot.call_count == 16
    assert mock_auto.mouse_click.call_count == 3
    assert mock_auto.click_element.call_count == 30


def test_enter_fuse_stops_when_screenshot_wait_fails():
    shop = Shop(TeamSetting(team_system=0))

    with (
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        _patch_two_attempt_screenshot_waiter() as mock_wait_for_screenshot,
    ):
        mock_auto.take_screenshot.return_value = None

        with pytest.raises(RuntimeError, match="等待截图超时"):
            shop.enter_fuse()

    mock_wait_for_screenshot.assert_called_once_with()
    assert mock_auto.take_screenshot.call_count == 2
    mock_auto.click_element.assert_not_called()


def test_standard_fusion_stops_when_inventory_screenshot_wait_fails():
    shop = Shop(TeamSetting(team_system=0))

    with (
        patch("tasks.mirror.in_shop.cfg") as mock_cfg,
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        _patch_two_attempt_screenshot_waiter() as mock_wait_for_screenshot,
    ):
        mock_cfg.set_win_size = 1440
        mock_auto.take_screenshot.return_value = None

        with pytest.raises(RuntimeError, match="等待截图超时"):
            shop.fuse_useless_gifts()

    mock_wait_for_screenshot.assert_called_once_with()
    assert mock_auto.take_screenshot.call_count == 2
    mock_auto.mouse_click.assert_not_called()
    mock_auto.click_element.assert_not_called()


def test_standard_fusion_stops_when_result_screenshot_wait_fails():
    shop = Shop(TeamSetting(team_system=0))

    def find_element(image_path, *args, **kwargs):
        if image_path == "candidate.png":
            return [(10, 10), (100, 100), (200, 200)]
        return None

    with (
        patch("tasks.mirror.in_shop.cfg") as mock_cfg,
        patch("tasks.mirror.in_shop.must_be_abandoned", ["candidate.png"]),
        patch("tasks.mirror.in_shop.sleep"),
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        _patch_two_attempt_screenshot_waiter() as mock_wait_for_screenshot,
    ):
        mock_cfg.set_win_size = 1440
        mock_auto.take_screenshot.side_effect = [object(), None, None]
        mock_auto.find_element.side_effect = find_element

        with pytest.raises(RuntimeError, match="等待截图超时"):
            shop.fuse_useless_gifts()

    assert mock_wait_for_screenshot.call_count == 2
    assert mock_auto.take_screenshot.call_count == 3
    assert mock_auto.mouse_click.call_count == 3
    mock_auto.click_element.assert_not_called()


def test_system_fusion_stops_when_result_screenshot_wait_fails():
    shop = Shop(TeamSetting(team_system=0))

    def find_element(image_path, *args, **kwargs):
        if image_path == "mirror/shop/fuse_label.png":
            return [(100, 100), (200, 200)]
        if image_path == f"mirror/shop/enhance_gifts/{shop.system}.png":
            return [(300, 150)]
        return None

    with (
        patch("tasks.mirror.in_shop.fusion_result", []),
        patch.object(shop, "enter_fuse"),
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        _patch_two_attempt_screenshot_waiter() as mock_wait_for_screenshot,
    ):
        mock_auto.find_element.side_effect = find_element
        mock_auto.take_screenshot.return_value = None

        with pytest.raises(RuntimeError, match="等待截图超时"):
            shop.fuse_system_gifts()

    mock_wait_for_screenshot.assert_called_once_with()
    assert mock_auto.take_screenshot.call_count == 2
    mock_auto.mouse_click.assert_called_once_with(300, 150)
    mock_auto.click_element.assert_not_called()


@pytest.mark.parametrize(
    "action",
    ["ego_gift_to_power_up", "buy_gifts", "sell_gifts", "enhance_gifts", "in_shop"],
)
def test_shop_action_stops_when_initial_screenshot_wait_fails(action):
    shop = Shop(TeamSetting(team_system=0))
    if action == "in_shop":
        shop.ignore_shop = [False] * 5

    with (
        patch("tasks.mirror.in_shop.cfg") as mock_cfg,
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        _patch_two_attempt_screenshot_waiter() as mock_wait_for_screenshot,
    ):
        mock_cfg.set_win_size = 1440
        mock_auto.take_screenshot.return_value = None

        with pytest.raises(RuntimeError, match="等待截图超时"):
            if action == "in_shop":
                shop.in_shop(1)
            else:
                getattr(shop, action)()

    mock_wait_for_screenshot.assert_called_once_with()
    assert mock_auto.take_screenshot.call_count == 2
    mock_auto.mouse_click.assert_not_called()
    mock_auto.click_element.assert_not_called()


def test_enhance_gifts_stops_when_main_loop_screenshot_wait_fails():
    shop = Shop(TeamSetting(team_system=0))

    with (
        patch("tasks.mirror.in_shop.cfg") as mock_cfg,
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        _patch_two_attempt_screenshot_waiter() as mock_wait_for_screenshot,
    ):
        mock_cfg.set_win_size = 1440
        mock_auto.take_screenshot.side_effect = [object(), None, None]
        mock_auto.find_element.return_value = (100, 100)

        with pytest.raises(RuntimeError, match="等待截图超时"):
            shop.enhance_gifts()

    assert mock_wait_for_screenshot.call_count == 2
    assert mock_auto.take_screenshot.call_count == 3
    assert mock_auto.mouse_click.call_count == 2
    mock_auto.click_element.assert_not_called()


def test_enhance_gifts_caps_repeated_entry_clicks():
    shop = Shop(TeamSetting(team_system=0))
    enter_enhance = "mirror/shop/enhance_gifts_assets.png"

    with (
        patch("tasks.mirror.in_shop.cfg") as mock_cfg,
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        patch("tasks.mirror.in_shop.retry", return_value=True),
        patch(
            "tasks.mirror.in_shop.wait_for_screenshot", return_value=object()
        ) as mock_wait,
        patch("tasks.mirror.in_shop.sleep"),
    ):
        mock_cfg.set_win_size = 1440
        mock_auto.find_element.return_value = None
        mock_auto.click_element.side_effect = lambda path, **kwargs: path == enter_enhance

        assert shop.enhance_gifts() is False

    assert mock_wait.call_count == 11
    assert mock_auto.click_element.call_count == 11
    assert all(
        call.args[0] == enter_enhance for call in mock_auto.click_element.call_args_list
    )
    mock_auto.mouse_click_blank.assert_not_called()


def test_shop_exit_stops_when_screenshot_wait_fails():
    shop = Shop(TeamSetting(team_system=0))
    shop.ignore_shop = [True] * 5

    with (
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        _patch_two_attempt_screenshot_waiter() as mock_wait_for_screenshot,
    ):
        mock_auto.take_screenshot.return_value = None

        with pytest.raises(RuntimeError, match="等待截图超时"):
            shop.in_shop(1)

    mock_wait_for_screenshot.assert_called_once_with()
    assert mock_auto.take_screenshot.call_count == 2
    mock_auto.mouse_click_blank.assert_called_once_with(times=3)
    mock_auto.click_element.assert_not_called()


def test_shop_exit_caps_repeated_confirm_clicks():
    shop = Shop(TeamSetting(team_system=0))
    shop.ignore_shop = [True] * 5
    leave_confirm = "mirror/shop/leave_shop_confirm_assets.png"

    with (
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        patch("tasks.mirror.in_shop.retry", return_value=True),
        patch("tasks.mirror.in_shop.wait_for_screenshot", return_value=object()),
        patch("tasks.mirror.in_shop.sleep"),
        patch("tasks.base.back_init_menu.back_init_menu") as mock_back_init_menu,
    ):
        mock_auto.find_element.return_value = None
        mock_auto.click_element.side_effect = lambda path, **kwargs: path == leave_confirm

        shop.in_shop(1)

    assert mock_auto.click_element.call_count == 31
    assert all(
        call.args[0] == leave_confirm for call in mock_auto.click_element.call_args_list
    )
    mock_back_init_menu.assert_called_once_with()


def test_buy_gifts_caps_repeated_level_three_purchases():
    shop = Shop(
        TeamSetting(
            team_system=0,
            shop_strategy=2,
            shopping_strategy=False,
            max_keyword_refresh=0,
            max_normal_refresh=0,
        )
    )
    level_three = "mirror/shop/level_III_to_buy.png"
    purchase_attempts = 0

    def click_element(image_path, **kwargs):
        nonlocal purchase_attempts
        if image_path == level_three:
            purchase_attempts += 1
            if purchase_attempts > 31:
                raise AssertionError("level III purchase loop was not bounded")
            return True
        return image_path in {
            "mirror/shop/purchase_assets.png",
            "mirror/road_in_mir/ego_gift_get_confirm_assets.png",
        }

    with (
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        patch("tasks.mirror.in_shop.wait_for_screenshot", return_value=object()),
        patch("tasks.mirror.in_shop.retry", return_value=True),
        patch("tasks.mirror.in_shop.sleep"),
    ):
        mock_auto.click_element.side_effect = click_element

        with pytest.raises(Shop.RestartGame):
            shop.buy_gifts()

    assert purchase_attempts == 31


def test_sell_gifts_caps_repeated_sell_entry_clicks():
    shop = Shop(TeamSetting(team_system=0))
    sell_entry = "mirror/shop/sell_gift_assets.png"
    sell_attempts = 0

    def click_element(image_path, **kwargs):
        nonlocal sell_attempts
        if image_path == sell_entry:
            sell_attempts += 1
            if sell_attempts > 64:
                raise AssertionError("sell entry loop was not bounded")
            return True
        return False

    with (
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        patch("tasks.mirror.in_shop.wait_for_screenshot", return_value=object()),
        patch("tasks.mirror.in_shop.retry", return_value=True),
    ):
        mock_auto.click_element.side_effect = click_element

        with pytest.raises(Shop.RestartGame):
            shop.sell_gifts()

    assert sell_attempts == 64


def test_standard_fusion_caps_repeated_result_claims():
    shop = Shop(TeamSetting(team_system=0))
    claim = "mirror/road_in_mir/ego_gift_get_confirm_assets.png"
    result = "mirror/shop/fuse_ego_gift_assets.png"
    result_attempts = 0

    def find_element(image_path, *args, **kwargs):
        if image_path == "candidate.png":
            return [(10, 10), (100, 100), (200, 200)]
        if image_path == claim:
            return (300, 300)
        return None

    def click_element(image_path, **kwargs):
        nonlocal result_attempts
        if image_path == result:
            result_attempts += 1
            if result_attempts > 31:
                raise AssertionError("standard fusion loop was not bounded")
            return True
        return image_path == claim

    with (
        patch("tasks.mirror.in_shop.must_be_abandoned", ["candidate.png"]),
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        patch("tasks.mirror.in_shop.wait_for_screenshot", return_value=object()),
        patch("tasks.mirror.in_shop.retry", return_value=True),
        patch("tasks.mirror.in_shop.sleep"),
    ):
        mock_auto.find_element.side_effect = find_element
        mock_auto.click_element.side_effect = click_element

        with pytest.raises(Shop.RestartGame):
            shop.fuse_useless_gifts()

    assert result_attempts == 31


def test_system_fusion_caps_repeated_result_claims():
    shop = Shop(TeamSetting(team_system=0))
    claim = "mirror/road_in_mir/ego_gift_get_confirm_assets.png"
    label = "mirror/shop/fuse_label.png"
    system_gifts = f"mirror/shop/enhance_gifts/{shop.system}.png"
    selections = 0

    def find_element(image_path, *args, **kwargs):
        if image_path == label:
            return [(100, 100), (200, 200)]
        if image_path == system_gifts:
            return [(300, 150)]
        return None

    def mouse_click(*args, **kwargs):
        nonlocal selections
        selections += 1
        if selections > 31:
            raise AssertionError("system fusion loop was not bounded")

    with (
        patch.object(shop, "enter_fuse", return_value=True),
        patch("tasks.mirror.in_shop.auto") as mock_auto,
        patch("tasks.mirror.in_shop.wait_for_screenshot", return_value=object()),
        patch("tasks.mirror.in_shop.retry", return_value=True),
    ):
        mock_auto.find_element.side_effect = find_element
        mock_auto.click_element.side_effect = lambda image_path, **kwargs: image_path == claim
        mock_auto.mouse_click.side_effect = mouse_click

        with pytest.raises(Shop.RestartGame):
            shop.fuse_system_gifts()

    assert selections == 31
