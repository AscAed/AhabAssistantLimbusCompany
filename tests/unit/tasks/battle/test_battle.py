from unittest.mock import call, patch

import numpy as np
import pytest

from tasks.battle.battle import Battle, BattleMode


def _battle() -> Battle:
    battle = object.__new__(Battle)
    battle.mouse_click_rate = False
    battle.defense_all_time = False
    battle.running = True
    return battle


@patch("tasks.battle.battle.ImageUtils.match_template")
@patch("tasks.battle.battle.ImageUtils.load_image")
@patch("tasks.battle.battle.auto.take_screenshot")
@patch(
    "tasks.battle.battle.auto.screenshot",
    new_callable=lambda: np.zeros((20, 20, 3), dtype=np.uint8),
)
def test_detect_battle_mode_prefers_higher_score(
    mock_screenshot,
    mock_take_screenshot,
    mock_load_image,
    mock_match_template,
):
    mock_take_screenshot.return_value = True

    continuous_template = np.ones((4, 4, 3), dtype=np.uint8)
    focused_template = np.ones((6, 6, 3), dtype=np.uint8)

    def fake_load_image(path, resize=False):
        if path.endswith("gear_left_continuous.png"):
            return continuous_template
        if path.endswith("gear_left_focused.png"):
            return focused_template
        return None

    def fake_match_template(_screenshot, template, _bbox, model="clam"):
        score = 0.91 if template.shape == continuous_template.shape else 0.82
        return (0, 0), score

    mock_load_image.side_effect = fake_load_image
    mock_match_template.side_effect = fake_match_template

    mode, scores = Battle._detect_battle_mode(retry_count=1)

    assert mode == BattleMode.CONTINUOUS
    assert scores[BattleMode.CONTINUOUS] == 0.91
    assert scores[BattleMode.FOCUSED] == 0.82


@patch.object(Battle, "_wait_for_pause", return_value=True)
@patch.object(Battle, "_start_continuous_defense", return_value=True)
@patch.object(Battle, "_detect_battle_mode", return_value=(BattleMode.CONTINUOUS, {BattleMode.CONTINUOUS: 0.95}))
@patch("tasks.battle.battle.auto.mouse_click_blank")
@patch("tasks.battle.battle.auto.key_press")
@patch("tasks.battle.battle.auto.click_element")
def test_first_turn_continuous_mode_uses_defense(
    mock_click_element,
    mock_key_press,
    mock_mouse_click_blank,
    _detect_battle_mode,
    _start_continuous_defense,
    _wait_for_pause,
):
    battle = _battle()

    result = battle._battle_operation(True, True, False)

    assert result is None
    _start_continuous_defense.assert_called_once()
    mock_key_press.assert_not_called()
    mock_click_element.assert_not_called()


@patch.object(Battle, "_wait_for_pause", side_effect=[False, True])
@patch.object(Battle, "_mouse_winrate_and_start")
@patch.object(Battle, "_detect_battle_mode", return_value=(BattleMode.FOCUSED, {BattleMode.FOCUSED: 0.94}))
@patch("tasks.battle.battle.auto.mouse_click_blank")
@patch("tasks.battle.battle.auto.key_press")
def test_focused_mode_uses_keyboard_then_mouse_fallback(
    mock_key_press,
    mock_mouse_click_blank,
    _detect_battle_mode,
    _mouse_winrate_and_start,
    _wait_for_pause,
):
    battle = _battle()

    result = battle._battle_operation(False, False, False)

    assert result is None
    assert mock_key_press.call_args_list == [call("p"), call("enter")]
    _mouse_winrate_and_start.assert_called_once()


@patch.object(Battle, "_wait_for_pause", return_value=True)
@patch.object(Battle, "_mouse_winrate_and_start")
@patch.object(Battle, "_detect_battle_mode", return_value=(BattleMode.FOCUSED, {BattleMode.FOCUSED: 0.92}))
@patch("tasks.battle.battle.auto.mouse_click_blank")
@patch("tasks.battle.battle.auto.key_press")
def test_first_turn_non_continuous_mode_still_uses_keyboard_then_mouse(
    mock_key_press,
    mock_mouse_click_blank,
    _detect_battle_mode,
    _mouse_winrate_and_start,
    _wait_for_pause,
):
    battle = _battle()

    result = battle._battle_operation(True, True, False)

    assert result is None
    assert mock_key_press.call_args_list == [call("p"), call("enter")]
    _mouse_winrate_and_start.assert_not_called()


@patch.object(Battle, "_wait_for_pause", return_value=True)
@patch.object(Battle, "_start_continuous_defense", return_value=True)
@patch.object(Battle, "_detect_battle_mode", return_value=(BattleMode.CONTINUOUS, {BattleMode.CONTINUOUS: 0.93}))
@patch("tasks.battle.battle.auto.mouse_click_blank")
@patch("tasks.battle.battle.auto.key_press")
def test_defense_all_time_continuous_uses_defense(
    mock_key_press,
    mock_mouse_click_blank,
    _detect_battle_mode,
    _start_continuous_defense,
    _wait_for_pause,
):
    battle = _battle()
    battle.defense_all_time = True

    result = battle._battle_operation(False, False, False)

    assert result is None
    _start_continuous_defense.assert_called_once()
    mock_key_press.assert_not_called()


@patch.object(Battle, "_wait_for_pause", side_effect=[False, True])
@patch.object(Battle, "_mouse_winrate_and_start")
@patch.object(Battle, "_detect_battle_mode", return_value=(BattleMode.FOCUSED, {BattleMode.FOCUSED: 0.93}))
@patch("tasks.battle.battle.auto.mouse_click_blank")
@patch("tasks.battle.battle.auto.key_press")
def test_defense_all_time_focused_uses_keyboard_then_mouse(
    mock_key_press,
    mock_mouse_click_blank,
    _detect_battle_mode,
    _mouse_winrate_and_start,
    _wait_for_pause,
):
    battle = _battle()
    battle.defense_all_time = True

    result = battle._battle_operation(False, False, False)

    assert result is None
    assert mock_key_press.call_args_list == [call("p"), call("enter")]
    _mouse_winrate_and_start.assert_called_once()


@patch.object(Battle, "_wait_for_pause", side_effect=[False, True])
@patch.object(Battle, "_defense_this_round", return_value=True)
@patch("tasks.battle.battle.auto.key_press")
def test_continuous_defense_uses_enter_when_drag_is_not_confirmed(
    mock_key_press,
    _defense_this_round,
    _wait_for_pause,
):
    battle = _battle()

    result = battle._start_continuous_defense()

    assert result is True
    _defense_this_round.assert_called_once()
    mock_key_press.assert_called_once_with("enter")


@patch("tasks.battle.battle.auto.mouse_to_blank")
@patch("tasks.battle.battle.auto.mouse_drag_link")
@patch("tasks.battle.battle.auto.mouse_click")
@patch("tasks.battle.battle.auto.find_element")
@patch("tasks.battle.battle.Battle._calculate_skills_position")
def test_defense_drag_targets_real_right_gear(
    mock_calculate,
    mock_find_element,
    mock_mouse_click,
    mock_mouse_drag_link,
    mock_mouse_to_blank,
):
    def fake_find_element(target, *args, **kwargs):
        if target == "battle/gear_left.png":
            return (100, 500)
        if target == "battle/gear_right.png":
            return (800, 500)
        return None

    def fake_calculate(skill_positions, gear_left, skill_nums, custom_tune=None):
        skill_positions.extend([[200, 600], [300, 600]])

    mock_find_element.side_effect = fake_find_element
    mock_calculate.side_effect = fake_calculate

    battle = _battle()
    result = battle._defense_this_round()

    assert result is True
    assert mock_mouse_click.call_args_list == [call(200, 600), call(300, 600)]
    mock_mouse_drag_link.assert_called_once()
    dragged_points = mock_mouse_drag_link.call_args.args[0]
    assert dragged_points[0] == (100, 500)
    assert dragged_points[1] == [200, 600]
    assert dragged_points[2] == [300, 600]
    assert dragged_points[-1] == [300, 600]
    resolve_last_position = mock_mouse_drag_link.call_args.kwargs["resolve_last_position"]
    with patch("tasks.battle.battle.auto.wait_until_appear", return_value=(800, 650)):
        assert resolve_last_position() == (800, 650)
    mock_mouse_to_blank.assert_called_once()


def test_mirror_death_wait_uses_outer_battle_timeout():
    class CaptureBudgetExceeded(BaseException):
        pass

    battle = _battle()
    battle.INIT_CHANCE = 16
    with (
        patch("tasks.battle.battle.cfg") as mock_cfg,
        patch("tasks.battle.battle.auto") as mock_auto,
        patch("tasks.base.screenshot.auto", new=mock_auto),
        patch(
            "tasks.base.retry.check_times",
            side_effect=[False, True],
        ) as mock_check_times,
        patch("tasks.base.back_init_menu.back_init_menu") as mock_back_init_menu,
    ):
        mock_cfg.fight_to_last_man = False
        mock_cfg.set_win_size = 1440
        mock_auto.get_restore_time.return_value = None
        mock_auto.take_screenshot.side_effect = [
            object(),
            object(),
            object(),
            CaptureBudgetExceeded("death-state loop skipped the outer timeout"),
        ]
        mock_auto.find_language_text.return_value = "dead"
        mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (
            True
            if target == "battle/in_mirror_assets.png"
            else (100, 100)
            if target == "battle/dead.png"
            else None
        )
        mock_auto.click_element.return_value = False

        assert battle.fight() is False

    assert mock_check_times.call_count == 2
    assert mock_auto.take_screenshot.call_count == 3
    mock_back_init_menu.assert_called_once()


def test_mirror_surrender_retries_after_settings_overlay_hides_death_marker():
    battle = _battle()
    battle.INIT_CHANCE = 16
    settings_open = False
    give_up_attempts = 0

    def fake_find_element(target, *args, **kwargs):
        if target == "battle/in_mirror_assets.png":
            return True
        if target == "battle/dead.png":
            return None if settings_open else (100, 100)
        if target == "battle/pause_assets.png":
            return settings_open
        return None

    def fake_click_element(target):
        nonlocal settings_open, give_up_attempts
        if target == "battle/give_up_assets.png":
            give_up_attempts += 1
            return settings_open and give_up_attempts == 2
        if target == "battle/setting_assets.png":
            settings_open = True
            return True
        return False

    with (
        patch("tasks.battle.battle.cfg") as mock_cfg,
        patch("tasks.battle.battle.auto") as mock_auto,
        patch("tasks.base.screenshot.auto", new=mock_auto),
        patch(
            "tasks.base.retry.check_times",
            return_value=False,
        ) as mock_check_times,
        patch("tasks.base.back_init_menu.back_init_menu") as mock_back_init_menu,
    ):
        mock_cfg.fight_to_last_man = False
        mock_cfg.set_win_size = 1440
        mock_auto.get_restore_time.return_value = None
        mock_auto.take_screenshot.side_effect = [object() for _ in range(4)]
        mock_auto.find_element.side_effect = fake_find_element
        mock_auto.find_language_text.return_value = "dead"
        mock_auto.click_element.side_effect = fake_click_element

        assert battle.fight() is False

    assert mock_check_times.call_count == 2
    assert mock_auto.find_language_text.call_count == 1
    assert give_up_attempts == 2
    mock_back_init_menu.assert_not_called()


def test_to_battle_stops_when_screenshot_wait_exhausts():
    with patch(
        "tasks.battle.battle.wait_for_screenshot",
        side_effect=RuntimeError("等待截图超时"),
    ) as wait_for_screenshot:
        assert Battle.to_battle() is False

    wait_for_screenshot.assert_called_once_with(max_attempts=16)


def test_battle_fight_propagates_screenshot_timeout():
    battle = _battle()
    battle.INIT_CHANCE = 16
    with patch(
        "tasks.battle.battle.wait_for_screenshot",
        side_effect=RuntimeError("等待截图超时"),
    ):
        with pytest.raises(RuntimeError, match="等待截图超时"):
            battle.fight()
