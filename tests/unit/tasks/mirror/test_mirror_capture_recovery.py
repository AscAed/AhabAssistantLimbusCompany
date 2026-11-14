from unittest.mock import patch

import pytest

from module.my_error.my_error import cannotOperateGameError
from tasks.mirror.mirror import Mirror


@patch("tasks.mirror.mirror.sleep", return_value=None)
@patch("tasks.mirror.mirror.wait_for_screenshot", return_value=None)
@patch("tasks.mirror.mirror.auto")
def test_initial_ego_scroll_stops_after_bounded_attempts(mock_auto, _wait, _sleep):
    slash_lookups = 0

    def find_element(target, *args, **kwargs):
        nonlocal slash_lookups
        if target == "mirror/road_to_mir/slash_gift_1.png":
            slash_lookups += 1
            if slash_lookups > 12:
                raise AssertionError("scroll loop exceeded its attempt limit")
            return (100, 100)
        return None

    mock_auto.click_element.return_value = False
    mock_auto.find_element.side_effect = find_element
    mirror = object.__new__(Mirror)
    mirror.system = "slash"
    mirror.opening_items = False
    mirror.observe_ego_gift = False
    mirror.observe_ego_gift_selected = []

    with pytest.raises(cannotOperateGameError, match="无法滚动定位初始EGO饰品"):
        mirror.select_init_ego_gift()

    assert mock_auto.mouse_drag.call_count == 12
    assert not any(
        "select_init_gift" in call.args[0]
        for call in mock_auto.click_element.call_args_list
    )


@patch("tasks.mirror.mirror.sleep", return_value=None)
@patch("tasks.mirror.mirror.retry", return_value=False)
@patch("tasks.mirror.mirror.wait_for_screenshot", return_value=None)
@patch("tasks.mirror.mirror.auto")
def test_initial_ego_scroll_accepts_target_on_last_attempt(mock_auto, _wait, _retry, _sleep):
    blunt_lookups = 0

    def find_element(target, *args, **kwargs):
        nonlocal blunt_lookups
        if target == "mirror/road_to_mir/slash_gift_1.png":
            return (100, 100)
        if target == "mirror/road_to_mir/blunt_gift_1_assets.png":
            blunt_lookups += 1
            return blunt_lookups == 12
        return None

    mock_auto.click_element.side_effect = lambda target, *args, **kwargs: target == (
        "mirror/road_to_mir/slash_gift_assets.png"
    )
    mock_auto.find_element.side_effect = find_element
    mirror = object.__new__(Mirror)
    mirror.system = "slash"
    mirror.opening_items = False
    mirror.observe_ego_gift = False
    mirror.observe_ego_gift_selected = []

    assert mirror.select_init_ego_gift() is False

    assert mock_auto.mouse_drag.call_count == 12
    selected_cards = [
        call.args[0]
        for call in mock_auto.click_element.call_args_list
        if "/select_init_gift/" in call.args[0]
    ]
    assert selected_cards == [
        "mirror/road_to_mir/select_init_gift/slash_ego_gift_1.png",
        "mirror/road_to_mir/select_init_gift/slash_ego_gift_2.png",
        "mirror/road_to_mir/select_init_gift/slash_ego_gift_3.png",
    ]


def test_observe_gift_selection_respects_three_item_limit():
    with (
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
        patch("tasks.mirror.mirror.ImageUtils") as mock_image_utils,
        patch("tasks.mirror.mirror.sleep"),
    ):
        mock_cfg.set_win_size = 1440
        mock_auto.take_screenshot.return_value = object()
        mock_auto.find_language_text.return_value = (1, 1)
        mock_image_utils.get_bbox.return_value = [100, 200, 1200, 1000]
        burn_marker_calls = 0
        selected_gift_lookups = []

        def find_element(target, *args, **kwargs):
            nonlocal burn_marker_calls
            if "observe_burn_assets.png" in target:
                burn_marker_calls += 1
                if burn_marker_calls == 1:
                    return (200, 100)
            if "Level_I.png" in target:
                selected_gift_lookups.append(target)
                return (500, 300)
            return None

        mock_auto.find_element.side_effect = find_element
        mirror = object.__new__(Mirror)
        mirror.observe_ego_gift_selected = [
            "burn_1_1_1",
            "bleed_1_1_1",
            "general_1_1_1",
            "tremor_1_1_1",
        ]

        mirror.select_observe_ego_gift()

        assert len(selected_gift_lookups) == 3


@patch("tasks.mirror.mirror.wait_for_screenshot", side_effect=RuntimeError("capture timeout"))
@patch("tasks.mirror.mirror.auto")
def test_road_to_mirror_stops_after_bounded_capture_failure(mock_auto, _wait):
    mirror = object.__new__(Mirror)

    with pytest.raises(RuntimeError, match="capture timeout"):
        mirror.road_to_mir()

    mock_auto.take_screenshot.assert_not_called()
    mock_auto.mouse_to_blank.assert_not_called()


def test_road_to_mirror_bounds_repeated_successful_drive_clicks():
    drive_clicks = 0

    def click_element(target, *args, **kwargs):
        nonlocal drive_clicks
        if target == "home/drive_assets.png":
            drive_clicks += 1
            if drive_clicks > 31:
                raise AssertionError("road_to_mir did not bound repeated drive clicks")
            return True
        return False

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot", return_value=None),
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.ImageUtils.load_image"),
        patch("tasks.mirror.mirror.ImageUtils.get_bbox", return_value=(0, 0, 100, 100)),
        patch("tasks.mirror.mirror.back_init_menu") as mock_back_init_menu,
    ):
        mock_auto.click_element.side_effect = click_element
        mock_auto.find_element.return_value = False
        mock_auto.find_text_element.return_value = True
        mirror = object.__new__(Mirror)

        mirror.road_to_mir()

    assert drive_clicks == 31
    mock_back_init_menu.assert_called_once_with()


@patch("tasks.mirror.mirror.wait_for_screenshot", side_effect=RuntimeError("capture timeout"))
@patch("tasks.mirror.mirror.auto")
def test_mirror_run_stops_after_bounded_capture_failure(mock_auto, _wait):
    mock_auto.click_element.return_value = False
    mock_auto.find_element.return_value = False
    mirror = object.__new__(Mirror)
    mirror.LOOP_COUNT = 250
    mirror.check_and_recover_process = lambda: False

    with pytest.raises(RuntimeError, match="capture timeout"):
        mirror.run()

    mock_auto.take_screenshot.assert_not_called()
    mock_auto.mouse_to_blank.assert_not_called()


def test_mirror_run_skips_dispatch_after_retry_restarts_game():
    with (
        patch("tasks.mirror.mirror.wait_for_screenshot") as mock_wait,
        patch(
            "tasks.mirror.mirror.retry",
            side_effect=[False, RuntimeError("next retry reached")],
        ),
        patch("tasks.mirror.mirror.PageStateDispatcher") as mock_dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        dispatcher = mock_dispatcher_type.return_value
        dispatcher.detect_state.side_effect = AssertionError(
            "state dispatch used the frame from before reconnect"
        )
        mock_cfg.floor_3_exit = False
        mock_auto.click_element.return_value = False
        mock_auto.find_element.return_value = False
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False

        with pytest.raises(RuntimeError, match="next retry reached"):
            mirror.run()

    assert mock_wait.call_count == 2
    dispatcher.detect_state.assert_not_called()


@patch("tasks.mirror.mirror.wait_for_screenshot", side_effect=RuntimeError("capture timeout"))
@patch("tasks.mirror.mirror.auto")
def test_enter_mirror_with_starlight_stops_after_capture_failure(mock_auto, _wait):
    mock_auto.find_element.return_value = (100, 100)
    mirror = object.__new__(Mirror)
    mirror.use_starlight = False
    mirror.opening_bonus = []

    with patch("tasks.mirror.mirror.cfg") as mock_cfg:
        mock_cfg.set_win_size = 1440
        with pytest.raises(RuntimeError, match="capture timeout"):
            mirror.enter_mir_with_star()

    mock_auto.take_screenshot.assert_not_called()
    mock_auto.mouse_action_with_pos.assert_not_called()


@patch("tasks.mirror.mirror.wait_for_screenshot", side_effect=RuntimeError("capture timeout"))
@patch("tasks.mirror.mirror.auto")
def test_select_initial_ego_stops_after_capture_failure(mock_auto, _wait):
    mirror = object.__new__(Mirror)
    mirror.system = "bleed"
    mirror.opening_items = False

    with pytest.raises(RuntimeError, match="capture timeout"):
        mirror.select_init_ego_gift()

    mock_auto.take_screenshot.assert_not_called()
    mock_auto.click_element.assert_not_called()


@patch("tasks.mirror.mirror.wait_for_screenshot", side_effect=RuntimeError("capture timeout"))
@patch("tasks.mirror.mirror.auto")
def test_restart_stops_after_capture_failure(mock_auto, _wait):
    mirror = object.__new__(Mirror)

    with pytest.raises(RuntimeError, match="capture timeout"):
        mirror.re_start()

    mock_auto.take_screenshot.assert_not_called()
    mock_auto.key_press.assert_not_called()


@patch("tasks.mirror.mirror.wait_for_screenshot", side_effect=RuntimeError("capture timeout"))
@patch("tasks.mirror.mirror.auto")
def test_event_handling_stops_after_capture_failure(mock_auto, _wait):
    mirror = object.__new__(Mirror)

    with pytest.raises(RuntimeError, match="capture timeout"):
        mirror.event_handling()

    mock_auto.take_screenshot.assert_not_called()
    mock_auto.click_element.assert_not_called()


def test_observe_gift_selection_skips_invalid_config_values():
    with (
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
        patch("tasks.mirror.mirror.ImageUtils"),
        patch("tasks.mirror.mirror.sleep"),
    ):
        mock_cfg.set_win_size = 1440
        mock_auto.take_screenshot.return_value = object()
        burn_marker_calls = 0

        def find_element(target, *args, **kwargs):
            nonlocal burn_marker_calls
            if "observe_burn_assets.png" in target:
                burn_marker_calls += 1
                if burn_marker_calls == 1:
                    return (200, 100)
            return None

        mock_auto.find_element.side_effect = find_element
        mirror = object.__new__(Mirror)
        mirror.observe_ego_gift_selected = [
            "unknown_1_1_1",
            "burn_4_1_1",
            "burn_1_0_1",
            "burn_1_1_9",
            "burn_1_1_1_extra",
        ]

        mirror.select_observe_ego_gift()

        mock_auto.mouse_click.assert_not_called()


@patch("tasks.mirror.mirror.wait_for_screenshot", side_effect=RuntimeError("capture timeout"))
@patch("tasks.mirror.mirror.auto")
def test_road_reward_collection_stops_after_capture_failure(mock_auto, _wait):
    mirror = object.__new__(Mirror)

    with pytest.raises(RuntimeError, match="capture timeout"):
        mirror.get_reward_in_road()

    mock_auto.take_screenshot.assert_not_called()
    mock_auto.click_element.assert_not_called()


@patch("tasks.mirror.reward_card.wait_for_screenshot", side_effect=RuntimeError("capture timeout"))
@patch("tasks.mirror.reward_card.auto")
def test_reward_card_selection_stops_after_capture_failure(mock_auto, _wait):
    from tasks.mirror.reward_card import get_reward_card

    with pytest.raises(RuntimeError, match="capture timeout"):
        get_reward_card()

    mock_auto.take_screenshot.assert_not_called()
    mock_auto.click_element.assert_not_called()


@patch("tasks.mirror.select_theme_pack.wait_for_screenshot", side_effect=RuntimeError("capture timeout"))
@patch("tasks.mirror.select_theme_pack.auto")
@patch("tasks.mirror.select_theme_pack.path_manager")
@patch("tasks.mirror.select_theme_pack.theme_list")
@patch("tasks.mirror.select_theme_pack.cfg")
def test_theme_pack_selection_stops_after_capture_failure(
    mock_cfg, mock_theme_list, mock_path_manager, mock_auto, _wait
):
    from tasks.mirror.select_theme_pack import select_theme_pack

    mock_cfg.set_win_size = 1080
    mock_path_manager.current_language = "zh_cn"
    mock_theme_list.get_effective_theme_pack_list.return_value = {}
    mock_auto.find_element.return_value = False

    with pytest.raises(RuntimeError, match="capture timeout"):
        select_theme_pack()

    mock_auto.take_screenshot.assert_not_called()
    mock_auto.click_element.assert_not_called()
