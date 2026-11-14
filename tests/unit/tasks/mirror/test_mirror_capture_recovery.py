from unittest.mock import patch

import pytest

from module.my_error.my_error import cannotOperateGameError
from tasks.mirror.mirror import (
    _MAX_EMPTY_SINNER_RECOVERIES,
    _MAX_SETUP_ITERATIONS,
    GameState,
    Mirror,
)


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


def test_mirror_run_returns_after_reward_claim_reaches_home_screen():
    complete_asset = "mirror/claim_reward/complete_mirror_100%_assets.png"
    home_asset = "home/drive_assets.png"
    with (
        patch("tasks.mirror.mirror.wait_for_screenshot"),
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        dispatcher_type.return_value.detect_state.return_value = GameState.CLAIM_REWARD
        mock_cfg.floor_3_exit = False
        mock_auto.click_element.side_effect = lambda target, *args, **kwargs: target == (
            "mirror/claim_reward/claim_rewards_assets.png"
        )
        mock_auto.find_element.side_effect = lambda target, *args, **kwargs: target in {
            "mirror/claim_reward/battle_statistics_assets.png",
            complete_asset,
            home_asset,
        }
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.bequest_from_the_previous_game = False
        mirror.floor = 0
        mirror.floor_times = [-9999.0] * 5
        mirror.battle_total_time = 0
        mirror.event_times = 0
        mirror.event_total_time = 0
        mirror.shop_total_time = 0
        mirror.find_road_total_time = 0
        mirror.system = "test"

        assert mirror.run() is True


def test_mirror_run_bounds_repeated_reward_confirm_clicks():
    screenshot_count = 0
    confirm_asset = "mirror/claim_reward/claim_rewards_confirm_assets.png"
    use_enkephalin_asset = "mirror/claim_reward/use_enkephalin_assets.png"

    def wait_for_capture():
        nonlocal screenshot_count
        screenshot_count += 1
        if screenshot_count > 32:
            raise AssertionError("reward loop exceeded its iteration limit")

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot", side_effect=wait_for_capture) as wait,
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        dispatcher_type.return_value.detect_state.return_value = GameState.CLAIM_REWARD
        mock_cfg.floor_3_exit = True
        mock_auto.click_element.side_effect = lambda target, *args, **kwargs: (
            target == confirm_asset
        )
        mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (
            target == use_enkephalin_asset
        )
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 0
        mirror.bequest_from_the_previous_game = False

        with pytest.raises(cannotOperateGameError, match="镜牢奖励领取"):
            mirror.run()

    assert wait.call_count == 32
    assert sum(call.args[0] == confirm_asset for call in mock_auto.click_element.call_args_list) == 31


@pytest.mark.parametrize(
    "action_asset",
    [
        "mirror/road_in_mir/forfeit_assets.png",
        "mirror/road_in_mir/setting_assets.png",
    ],
)
def test_mirror_run_bounds_repeated_floor_three_exit_actions(action_asset):
    action_count = 0
    confirm_asset = "mirror/road_in_mir/towindow&forfeit_confirm_assets.png"

    def click_element(target, *args, **kwargs):
        nonlocal action_count
        if target == action_asset:
            action_count += 1
            if action_count > 31:
                raise AssertionError("floor-exit flow exceeded its action limit")
            return True
        return False

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher"),
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        mock_cfg.floor_3_exit = True
        mock_auto.find_element.return_value = False
        mock_auto.click_element.side_effect = click_element
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 4

        with pytest.raises(cannotOperateGameError, match="只打三层退出操作次数超限"):
            mirror.run()

    assert action_count == 31
    assert mock_wait.call_count == 32
    assert sum(
        call.args[0] == confirm_asset for call in mock_auto.click_element.call_args_list
    ) == 32


def test_mirror_run_accepts_exit_confirmation_after_last_allowed_action():
    action_count = 0
    screenshot_count = 0
    confirm_asset = "mirror/road_in_mir/towindow&forfeit_confirm_assets.png"
    forfeit_asset = "mirror/road_in_mir/forfeit_assets.png"

    def wait_for_screenshot():
        nonlocal screenshot_count
        screenshot_count += 1

    def click_element(target, *args, **kwargs):
        nonlocal action_count
        if target == confirm_asset:
            return screenshot_count == 32
        if target == forfeit_asset:
            action_count += 1
            return True
        return False

    with (
        patch(
            "tasks.mirror.mirror.wait_for_screenshot",
            side_effect=wait_for_screenshot,
        ) as mock_wait,
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher"),
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        mock_cfg.floor_3_exit = True
        mock_auto.find_element.return_value = False
        mock_auto.click_element.side_effect = click_element
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 4
        mirror.bequest_from_the_previous_game = True
        mirror.get_reward_in_road = lambda: True

        assert mirror.run() is True

    assert action_count == 31
    assert mock_wait.call_count == 32


def test_mirror_run_bounds_floor_three_exit_when_controls_are_not_recognized():
    screenshot_count = 0

    def wait_for_screenshot():
        nonlocal screenshot_count
        screenshot_count += 1
        if screenshot_count > 63:
            raise AssertionError("floor-exit loop exceeded its iteration limit")

    with (
        patch(
            "tasks.mirror.mirror.wait_for_screenshot",
            side_effect=wait_for_screenshot,
        ) as mock_wait,
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        dispatcher_type.return_value.detect_state.return_value = GameState.ROAD_MAP
        mock_cfg.floor_3_exit = True
        mock_auto.click_element.return_value = False
        mock_auto.find_element.return_value = False
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 4
        mirror.get_floor_num = False

        with pytest.raises(
            cannotOperateGameError,
            match="只打三层连续未识别退出操作次数超限",
        ):
            mirror.run()

    assert mock_wait.call_count == 63
    assert dispatcher_type.return_value.detect_state.call_count == 32


def test_mirror_run_accepts_floor_three_exit_confirmation_after_no_action_limit():
    screenshot_count = 0
    confirm_asset = "mirror/road_in_mir/towindow&forfeit_confirm_assets.png"

    def wait_for_screenshot():
        nonlocal screenshot_count
        screenshot_count += 1

    def click_element(target, *args, **kwargs):
        return target == confirm_asset and screenshot_count == 63

    with (
        patch(
            "tasks.mirror.mirror.wait_for_screenshot",
            side_effect=wait_for_screenshot,
        ) as mock_wait,
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        dispatcher_type.return_value.detect_state.return_value = GameState.ROAD_MAP
        mock_cfg.floor_3_exit = True
        mock_auto.click_element.side_effect = click_element
        mock_auto.find_element.return_value = False
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 4
        mirror.get_floor_num = False
        mirror.bequest_from_the_previous_game = True
        mirror.get_reward_in_road = lambda: True

        assert mirror.run() is True

    assert mock_wait.call_count == 63
    assert dispatcher_type.return_value.detect_state.call_count == 31


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


@pytest.mark.parametrize(
    ("use_starlight", "continue_asset"),
    [
        (True, "mirror/road_to_mir/dreaming_star/no_convert_star_to_cost_assets.png"),
        (False, "mirror/road_to_mir/dreaming_star/convert_star_to_cost_assets.png"),
        (False, "mirror/road_to_mir/dreaming_star/dreaming_star_enter_assets.png"),
    ],
)
def test_enter_mirror_with_starlight_bounds_repeated_actions(
    use_starlight, continue_asset
):
    with (
        patch("tasks.mirror.mirror.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        mock_cfg.set_win_size = 1440
        mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (
            (100, 100)
            if target == "mirror/road_to_mir/dreaming_star/coins_assets.png"
            else False
        )
        mock_auto.click_element.side_effect = (
            lambda target, *args, **kwargs: target == continue_asset
        )
        mirror = object.__new__(Mirror)
        mirror.use_starlight = use_starlight
        mirror.opening_bonus = []

        with pytest.raises(cannotOperateGameError, match="操作次数超限"):
            mirror.enter_mir_with_star()

    assert mock_wait.call_count == _MAX_SETUP_ITERATIONS
    assert sum(
        call.args[0] == continue_asset for call in mock_auto.click_element.call_args_list
    ) == _MAX_SETUP_ITERATIONS


def test_enter_mirror_with_starlight_accepts_success_on_last_iteration():
    with (
        patch("tasks.mirror.mirror.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        mock_cfg.set_win_size = 1440
        state_lookups = 0

        def find_element(target, *args, **kwargs):
            nonlocal state_lookups
            if target == "mirror/road_to_mir/dreaming_star/coins_assets.png":
                return (100, 100)
            state_lookups += 1
            return state_lookups == _MAX_SETUP_ITERATIONS

        mock_auto.find_element.side_effect = find_element
        mirror = object.__new__(Mirror)
        mirror.use_starlight = False
        mirror.opening_bonus = []

        assert mirror.enter_mir_with_star() is None

    assert mock_wait.call_count == _MAX_SETUP_ITERATIONS


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


def test_select_initial_ego_bounds_repeated_confirmation_clicks():
    confirm_asset = "mirror/road_to_mir/select_init_ego_gifts_confirm_assets.png"
    with (
        patch("tasks.mirror.mirror.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.mirror.auto") as mock_auto,
    ):
        mock_auto.click_element.side_effect = (
            lambda target, *args, **kwargs: target
            == "mirror/road_in_mir/ego_gift_get_confirm_assets.png"
        )
        mirror = object.__new__(Mirror)
        mirror.system = "bleed"
        mirror.opening_items = False

        with pytest.raises(cannotOperateGameError, match="操作次数超限"):
            mirror.select_init_ego_gift()

    assert mock_wait.call_count == _MAX_SETUP_ITERATIONS
    assert sum(
        call.args[0] == "mirror/road_in_mir/ego_gift_get_confirm_assets.png"
        for call in mock_auto.click_element.call_args_list
    ) == _MAX_SETUP_ITERATIONS
    assert not any(call.args[0] == confirm_asset for call in mock_auto.click_element.call_args_list)


def test_select_initial_ego_accepts_success_on_last_iteration():
    with (
        patch("tasks.mirror.mirror.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.auto") as mock_auto,
    ):
        state_lookups = 0

        def find_element(target, *args, **kwargs):
            nonlocal state_lookups
            state_lookups += 1
            return state_lookups == (3 * (_MAX_SETUP_ITERATIONS - 1)) + 1

        mock_auto.find_element.side_effect = find_element
        mock_auto.click_element.return_value = False
        mirror = object.__new__(Mirror)
        mirror.system = "bleed"
        mirror.opening_items = False
        mirror.observe_ego_gift = False
        mirror.observe_ego_gift_selected = []

        assert mirror.select_init_ego_gift() is None

    assert mock_wait.call_count == _MAX_SETUP_ITERATIONS


@patch("tasks.mirror.mirror.wait_for_screenshot", side_effect=RuntimeError("capture timeout"))
@patch("tasks.mirror.mirror.auto")
def test_restart_stops_after_capture_failure(mock_auto, _wait):
    mirror = object.__new__(Mirror)

    with pytest.raises(RuntimeError, match="capture timeout"):
        mirror.re_start()

    mock_auto.take_screenshot.assert_not_called()
    mock_auto.key_press.assert_not_called()


def test_restart_bounds_repeated_forfeit_clicks():
    max_attempts = 31
    confirm_asset = "mirror/road_in_mir/towindow&forfeit_confirm_assets.png"
    forfeit_asset = "mirror/road_in_mir/forfeit_assets.png"
    click_count = 0

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.mirror.auto") as mock_auto,
    ):

        def click_element(target, *args, **kwargs):
            nonlocal click_count
            if target == confirm_asset:
                return False
            if target == forfeit_asset:
                click_count += 1
                if click_count > max_attempts:
                    raise AssertionError("restart loop exceeded its action limit")
                return True
            return False

        mock_auto.click_element.side_effect = click_element
        mirror = object.__new__(Mirror)

        with pytest.raises(cannotOperateGameError, match="操作次数超限"):
            mirror.re_start()

    assert mock_wait.call_count == max_attempts
    assert click_count == max_attempts
    mock_auto.key_press.assert_not_called()


def test_restart_accepts_confirmation_on_last_attempt():
    max_attempts = 31
    confirm_asset = "mirror/road_in_mir/towindow&forfeit_confirm_assets.png"
    forfeit_asset = "mirror/road_in_mir/forfeit_assets.png"
    screenshot_count = 0

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.mirror.auto") as mock_auto,
    ):

        def wait_for_screenshot():
            nonlocal screenshot_count
            screenshot_count += 1

        def click_element(target, *args, **kwargs):
            if target == confirm_asset:
                return screenshot_count == max_attempts
            if target == forfeit_asset:
                return screenshot_count < max_attempts
            return False

        mock_wait.side_effect = wait_for_screenshot
        mock_auto.click_element.side_effect = click_element
        mirror = object.__new__(Mirror)
        mirror.first_battle = False
        mirror.start_time = 0

        mirror.re_start()

    assert mock_wait.call_count == max_attempts
    assert screenshot_count == max_attempts
    assert mirror.first_battle is True
    mock_auto.key_press.assert_not_called()


@patch("tasks.mirror.mirror.wait_for_screenshot", side_effect=RuntimeError("capture timeout"))
@patch("tasks.mirror.mirror.auto")
def test_event_handling_stops_after_capture_failure(mock_auto, _wait):
    mirror = object.__new__(Mirror)

    with pytest.raises(RuntimeError, match="capture timeout"):
        mirror.event_handling()

    mock_auto.take_screenshot.assert_not_called()
    mock_auto.click_element.assert_not_called()


@pytest.mark.parametrize("transition_after_limit", [False, True])
def test_event_handling_caps_repeated_continue_clicks(transition_after_limit):
    max_attempts = 31
    with (
        patch("tasks.mirror.mirror.wait_for_screenshot") as mock_wait,
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.back_init_menu") as mock_back,
        patch("tasks.mirror.mirror.auto") as mock_auto,
    ):
        mirror = object.__new__(Mirror)
        mirror.event_total_time = 0
        mirror.event_times = 0
        continue_clicks = 0

        def find_element(target, *args, **kwargs):
            if target == "battle/turn_assets.png" and transition_after_limit:
                return continue_clicks == max_attempts
            return False

        def click_element(target, *args, **kwargs):
            nonlocal continue_clicks
            if target == "event/continue_assets.png":
                continue_clicks += 1
                if continue_clicks > max_attempts:
                    raise AssertionError("event loop exceeded its action limit")
                return True
            return False

        mock_auto.find_element.side_effect = find_element
        mock_auto.click_element.side_effect = click_element

        mirror.event_handling()

    assert mock_wait.call_count == max_attempts + 1
    assert continue_clicks == max_attempts
    if transition_after_limit:
        mock_back.assert_not_called()
    else:
        mock_back.assert_called_once_with()
    assert mirror.event_times == 1


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


def test_road_reward_collection_bounds_repeated_confirm_clicks():
    screenshot_count = 0
    confirm_asset = "mirror/claim_reward/claim_rewards_confirm_assets.png"

    def wait_for_capture():
        nonlocal screenshot_count
        screenshot_count += 1
        if screenshot_count > 31:
            raise AssertionError("reward collection exceeded its iteration limit")

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot", side_effect=wait_for_capture) as wait,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        mock_cfg.no_weekly_bonuses = False
        mock_cfg.hard_mirror_single_bonuses = False
        mock_auto.click_element.side_effect = lambda target, *args, **kwargs: (
            target == confirm_asset
        )
        mirror = object.__new__(Mirror)

        with pytest.raises(cannotOperateGameError, match="镜牢奖励领取"):
            mirror.get_reward_in_road()

    assert wait.call_count == 31
    assert sum(call.args[0] == confirm_asset for call in mock_auto.click_element.call_args_list) == 31


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


@patch("tasks.mirror.reward_card.wait_for_screenshot")
@patch("tasks.mirror.reward_card.auto")
def test_reward_card_selection_bounds_repeated_continue_clicks(mock_auto, mock_wait):
    from tasks.mirror.reward_card import _MAX_REWARD_CARD_ITERATIONS, get_reward_card

    continue_asset = "mirror/get_reward_card/continue_choosing_assets.png"
    mock_auto.find_element.return_value = None
    mock_auto.click_element.side_effect = lambda target, *args, **kwargs: target == continue_asset

    with pytest.raises(cannotOperateGameError, match="镜牢奖励领取出错"):
        get_reward_card()

    assert mock_wait.call_count == _MAX_REWARD_CARD_ITERATIONS
    assert sum(call.args[0] == continue_asset for call in mock_auto.click_element.call_args_list) == (
        _MAX_REWARD_CARD_ITERATIONS
    )


@patch("tasks.mirror.reward_card.retry", return_value=True)
@patch("tasks.mirror.reward_card.wait_for_screenshot")
@patch("tasks.mirror.reward_card.auto")
def test_reward_card_selection_accepts_success_on_last_iteration(mock_auto, mock_wait, _retry):
    from tasks.mirror.reward_card import _MAX_REWARD_CARD_ITERATIONS, get_reward_card

    completed_iterations = 0

    def wait_for_screenshot():
        nonlocal completed_iterations
        completed_iterations += 1

    def find_element(target, *args, **kwargs):
        if target == "mirror/road_in_mir/legend_assets.png":
            return completed_iterations == _MAX_REWARD_CARD_ITERATIONS
        return None

    mock_wait.side_effect = wait_for_screenshot
    mock_auto.find_element.side_effect = find_element
    mock_auto.click_element.return_value = False

    assert get_reward_card() is True
    assert completed_iterations == _MAX_REWARD_CARD_ITERATIONS


def test_mirror_run_bounds_repeated_road_map_ego_gift_confirm_clicks():
    confirm_asset = "mirror/road_in_mir/ego_gift_get_confirm_assets.png"
    confirm_clicks = 0

    def click_element(target, *args, **kwargs):
        nonlocal confirm_clicks
        if target == confirm_asset:
            confirm_clicks += 1
            if confirm_clicks > 31:
                raise AssertionError("road-map confirmation exceeded its action limit")
            return True
        return False

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot"),
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        dispatcher_type.return_value.detect_state.return_value = GameState.ROAD_MAP
        mock_cfg.floor_3_exit = False
        mock_auto.click_element.side_effect = click_element
        mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (
            target == confirm_asset
        )
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 0
        mirror.get_floor_num = False

        with pytest.raises(cannotOperateGameError, match="EGO饰品确认操作次数超限"):
            mirror.run()

    assert confirm_clicks == 31


def test_mirror_run_accepts_road_map_transition_after_last_ego_gift_confirm():
    confirm_asset = "mirror/road_in_mir/ego_gift_get_confirm_assets.png"
    claim_asset = "mirror/claim_reward/claim_rewards_assets.png"
    complete_asset = "mirror/claim_reward/complete_mirror_100%_assets.png"
    confirm_clicks = 0
    state_detections = 0
    current_state = GameState.ROAD_MAP

    def detect_state():
        nonlocal current_state, state_detections
        state_detections += 1
        if state_detections > 32:
            current_state = GameState.CLAIM_REWARD
        return current_state

    def click_element(target, *args, **kwargs):
        nonlocal confirm_clicks
        if target == confirm_asset:
            confirm_clicks += 1
            return confirm_clicks <= 31
        return False

    def find_element(target, *args, **kwargs):
        return current_state == GameState.CLAIM_REWARD and target in {
            claim_asset,
            complete_asset,
        }

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot"),
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        dispatcher_type.return_value.detect_state.side_effect = detect_state
        mock_cfg.floor_3_exit = False
        mock_auto.click_element.side_effect = click_element
        mock_auto.find_element.side_effect = find_element
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 0
        mirror.get_floor_num = False
        mirror.bequest_from_the_previous_game = True
        mirror.get_reward_in_road = lambda: True

        assert mirror.run() is True

    assert confirm_clicks == 32


@pytest.mark.parametrize("close_click_result", [True, False])
def test_mirror_run_bounds_repeated_infinity_popup_close_attempts(close_click_result):
    popup_asset = "mirror/infinity_mirror_assets.png"
    close_asset = "mirror/infinity_mirror_close_assets.png"
    close_attempts = 0

    def click_element(target, *args, **kwargs):
        nonlocal close_attempts
        if target == close_asset:
            close_attempts += 1
            if close_attempts > 31:
                raise AssertionError("Infinity Mirror popup exceeded its action limit")
            return close_click_result
        return False

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot"),
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
        patch("tasks.mirror.mirror.battle") as mock_battle,
    ):
        dispatcher_type.return_value.detect_state.return_value = None
        mock_cfg.floor_3_exit = False
        mock_battle.fail_times = 0
        mock_auto.click_element.side_effect = click_element
        mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (
            target == popup_asset
        )
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 0
        mirror.get_floor_num = False

        with pytest.raises(cannotOperateGameError, match="无限镜牢弹窗关闭操作次数超限"):
            mirror.run()

    assert close_attempts == 31


def test_mirror_run_accepts_infinity_popup_close_on_last_attempt():
    popup_asset = "mirror/infinity_mirror_assets.png"
    close_asset = "mirror/infinity_mirror_close_assets.png"
    screenshot_count = 0
    close_attempts = 0

    def wait_for_screenshot():
        nonlocal screenshot_count
        screenshot_count += 1
        if screenshot_count > 32:
            raise RuntimeError("popup closed")

    def find_element(target, *args, **kwargs):
        return target == popup_asset and screenshot_count <= 31

    def click_element(target, *args, **kwargs):
        nonlocal close_attempts
        if target == close_asset:
            close_attempts += 1
            return True
        return False

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot", side_effect=wait_for_screenshot),
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
        patch("tasks.mirror.mirror.battle") as mock_battle,
    ):
        dispatcher_type.return_value.detect_state.return_value = None
        mock_cfg.floor_3_exit = False
        mock_battle.fail_times = 0
        mock_auto.click_element.side_effect = click_element
        mock_auto.find_element.side_effect = find_element
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 0
        mirror.get_floor_num = False

        with pytest.raises(RuntimeError, match="popup closed"):
            mirror.run()

    assert close_attempts == 31


def test_mirror_run_bounds_infinity_popup_when_dispatcher_consumes_loop():
    popup_asset = "mirror/infinity_mirror_assets.png"
    close_asset = "mirror/infinity_mirror_close_assets.png"
    screenshot_count = 0

    def wait_for_screenshot():
        nonlocal screenshot_count
        screenshot_count += 1
        if screenshot_count > 94:
            raise AssertionError("popup handling exceeded its visible-iteration limit")

    with (
        patch(
            "tasks.mirror.mirror.wait_for_screenshot",
            side_effect=wait_for_screenshot,
        ) as mock_wait,
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        dispatcher_type.return_value.detect_state.return_value = GameState.ROAD_MAP
        mock_cfg.floor_3_exit = False
        mock_auto.click_element.return_value = False
        mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (
            target == popup_asset
        )
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 0
        mirror.get_floor_num = False

        with pytest.raises(cannotOperateGameError, match="无限镜牢弹窗关闭操作次数超限"):
            mirror.run()

    assert mock_wait.call_count == 94
    assert not any(
        call.args[0] == close_asset for call in mock_auto.click_element.call_args_list
    )


def test_mirror_run_bounds_road_map_when_route_markers_disappear():
    screenshot_count = 0

    def wait_for_screenshot():
        nonlocal screenshot_count
        screenshot_count += 1
        if screenshot_count > 96:
            raise AssertionError("road-map loop exceeded its no-marker limit")

    with (
        patch(
            "tasks.mirror.mirror.wait_for_screenshot",
            side_effect=wait_for_screenshot,
        ) as mock_wait,
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        dispatcher_type.return_value.detect_state.return_value = GameState.ROAD_MAP
        mock_cfg.floor_3_exit = False
        mock_auto.click_element.return_value = False
        mock_auto.find_element.return_value = False
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 0
        mirror.get_floor_num = False

        with pytest.raises(
            cannotOperateGameError,
            match="镜牢路线图连续未识别路线标记次数超限",
        ):
            mirror.run()

    assert mock_wait.call_count == 96


def test_mirror_run_bounds_repeated_empty_sinner_formation_retries():
    empty_sinner_asset = "teams/none_sinner_assets.png"
    empty_sinner_clicks = 0
    formation_calls = 0
    state_detections = 0

    def click_element(target, *args, **kwargs):
        nonlocal empty_sinner_clicks
        if target == empty_sinner_asset:
            empty_sinner_clicks += 1
            if empty_sinner_clicks > _MAX_EMPTY_SINNER_RECOVERIES:
                raise AssertionError("empty-sinner recovery exceeded its retry limit")
            return True
        return False

    def team_formation(_sinner_team):
        nonlocal formation_calls
        formation_calls += 1
        return True

    def detect_state():
        nonlocal state_detections
        state_detections += 1
        if state_detections % 3 == 0:
            return GameState.UNKNOWN
        return GameState.BATTLE_FORMATION

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot"),
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
        patch("tasks.mirror.mirror.team_formation", side_effect=team_formation),
    ):
        dispatcher_type.return_value.detect_state.side_effect = detect_state
        mock_cfg.floor_3_exit = False
        mock_auto.click_element.side_effect = click_element
        mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (
            target == empty_sinner_asset
        )
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.first_battle = True
        mirror.floor = 0
        mirror.get_floor_num = False
        mirror.sinner_team = [1, 2, 3]

        with pytest.raises(
            cannotOperateGameError,
            match="镜牢队伍编队空位修复次数超限",
        ):
            mirror.run()

    assert empty_sinner_clicks == _MAX_EMPTY_SINNER_RECOVERIES
    assert formation_calls == _MAX_EMPTY_SINNER_RECOVERIES + 1


def test_mirror_run_bounds_repeated_unselected_sinner_popup_retries():
    unselected_sinner_asset = "battle/select_none_assets.png"
    popup_dismissals = 0

    def dismiss_popup():
        nonlocal popup_dismissals
        popup_dismissals += 1

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot"),
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
        patch("tasks.mirror.mirror.battle") as mock_battle,
    ):
        dispatcher_type.return_value.detect_state.return_value = GameState.UNKNOWN
        mock_cfg.floor_3_exit = False
        mock_battle.fail_times = 0
        mock_auto.click_element.return_value = False
        mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (
            target == unselected_sinner_asset
        )
        mock_auto.mouse_click_blank.side_effect = dismiss_popup
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.first_battle = False
        mirror.floor = 0
        mirror.get_floor_num = False

        with pytest.raises(
            cannotOperateGameError,
            match="镜牢队伍编队空位修复次数超限",
        ):
            mirror.run()

    assert popup_dismissals == _MAX_EMPTY_SINNER_RECOVERIES


def test_mirror_run_accepts_transition_after_last_empty_sinner_reformation():
    empty_sinner_asset = "teams/none_sinner_assets.png"
    complete_mirror_asset = "mirror/claim_reward/complete_mirror_100%_assets.png"
    state_detections = 0
    empty_sinner_clicks = 0
    formation_calls = 0
    max_recoveries = _MAX_EMPTY_SINNER_RECOVERIES

    def detect_state():
        nonlocal state_detections
        state_detections += 1
        if state_detections <= (max_recoveries * 2) + 1:
            return GameState.BATTLE_FORMATION
        return GameState.CLAIM_REWARD

    def click_element(target, *args, **kwargs):
        nonlocal empty_sinner_clicks
        if target == empty_sinner_asset:
            empty_sinner_clicks += 1
            return True
        return False

    def team_formation(_sinner_team):
        nonlocal formation_calls
        formation_calls += 1
        return True

    def find_element(target, *args, **kwargs):
        return (
            target == empty_sinner_asset
            and state_detections <= (max_recoveries * 2) + 1
        ) or (
            target
            in {
                "mirror/claim_reward/claim_rewards_assets.png",
                complete_mirror_asset,
            }
            and state_detections > (max_recoveries * 2) + 1
        )

    with (
        patch("tasks.mirror.mirror.wait_for_screenshot"),
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
        patch("tasks.mirror.mirror.team_formation", side_effect=team_formation),
    ):
        dispatcher_type.return_value.detect_state.side_effect = detect_state
        mock_cfg.floor_3_exit = False
        mock_auto.click_element.side_effect = click_element
        mock_auto.find_element.side_effect = find_element
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.first_battle = True
        mirror.floor = 0
        mirror.get_floor_num = False
        mirror.sinner_team = [1, 2, 3]
        mirror.bequest_from_the_previous_game = True
        mirror.get_reward_in_road = lambda: True

        assert mirror.run() is True

    assert empty_sinner_clicks == _MAX_EMPTY_SINNER_RECOVERIES
    assert formation_calls == _MAX_EMPTY_SINNER_RECOVERIES + 1


def test_mirror_run_recovers_road_map_marker_after_retry_limit():
    screenshot_count = 0
    search_calls = 0
    legend_asset = "mirror/road_in_mir/legend_assets.png"

    def wait_for_screenshot():
        nonlocal screenshot_count
        screenshot_count += 1
        if screenshot_count > 96:
            raise RuntimeError("route marker restored")

    def find_element(target, *args, **kwargs):
        return target == legend_asset and screenshot_count == 96

    def search_road():
        nonlocal search_calls
        search_calls += 1

    with (
        patch(
            "tasks.mirror.mirror.wait_for_screenshot",
            side_effect=wait_for_screenshot,
        ),
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        dispatcher_type.return_value.detect_state.return_value = GameState.ROAD_MAP
        mock_cfg.floor_3_exit = False
        mock_auto.click_element.return_value = False
        mock_auto.find_element.side_effect = find_element
        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 250
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 0
        mirror.get_floor_num = False
        mirror.find_road_total_time = 0
        mirror.search_road = search_road
        mirror._time_call = lambda function, *args: (function(*args), 0)

        with pytest.raises(RuntimeError, match="route marker restored"):
            mirror.run()

    assert search_calls == 1
