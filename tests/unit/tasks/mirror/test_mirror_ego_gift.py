from unittest.mock import patch

import pytest

from module.my_error.my_error import cannotOperateGameError
from tasks.mirror.mirror import Mirror


@patch(
    "tasks.mirror.mirror.wait_for_screenshot",
    side_effect=RuntimeError("等待截图超时"),
)
@patch("tasks.mirror.mirror.auto")
@patch("tasks.mirror.mirror.cfg")
def test_acquire_ego_gift_stops_before_input_when_screenshot_wait_fails(
    mock_cfg, mock_auto, mock_wait_for_screenshot
):
    mock_cfg.set_win_size = 1440
    mock_auto.take_screenshot.side_effect = AssertionError(
        "unbounded capture path used"
    )
    mirror = object.__new__(Mirror)

    with pytest.raises(RuntimeError, match="等待截图超时"):
        mirror.acquire_ego_gift()

    mock_wait_for_screenshot.assert_called_once_with()
    mock_auto.take_screenshot.assert_not_called()
    mock_auto.mouse_click.assert_not_called()
    mock_auto.click_element.assert_not_called()


@patch("tasks.mirror.mirror.retry", return_value=True)
@patch("tasks.mirror.mirror.time.sleep", return_value=None)
@patch("tasks.mirror.mirror.sleep", return_value=None)
@patch("tasks.mirror.mirror.auto")
@patch("tasks.mirror.mirror.cfg")
def test_acquire_ego_gift_refuse_path_returns_none(mock_cfg, mock_auto, mock_sleep, mock_time_sleep, mock_retry):
    mock_cfg.set_win_size = 1440
    mock_auto.find_element.return_value = (1000, 1000)

    mirror = object.__new__(Mirror)
    result = mirror.acquire_ego_gift(type=2)

    assert result is None
    mock_auto.mouse_click.assert_any_call(500, 500)
    mock_auto.mouse_click.assert_any_call(1000, 500)
    mock_auto.click_element.assert_called_once_with(
        "mirror/road_in_mir/acquire_ego_gift_select_assets.png",
        model="normal",
    )


@patch("tasks.mirror.mirror.wait_for_screenshot", return_value=None)
@patch("tasks.mirror.mirror.auto")
@patch("tasks.mirror.mirror.cfg")
def test_acquire_ego_gift_bounds_repeated_recognition_errors(mock_cfg, mock_auto, mock_wait):
    mock_cfg.set_win_size = 1440
    mock_auto.click_element.return_value = False
    mock_auto.find_element.side_effect = RuntimeError("recognition failed")
    mirror = object.__new__(Mirror)

    with pytest.raises(cannotOperateGameError, match="操作次数超限"):
        mirror.acquire_ego_gift()

    assert mock_wait.call_count == 31
    assert mock_auto.click_element.call_count == 31
    assert mock_auto.find_element.call_count == 31


@patch("tasks.mirror.mirror.wait_for_screenshot", return_value=None)
@patch("tasks.mirror.mirror.auto")
@patch("tasks.mirror.mirror.cfg")
def test_acquire_ego_gift_accepts_confirmation_on_last_iteration(mock_cfg, mock_auto, mock_wait):
    mock_cfg.set_win_size = 1440
    mock_auto.click_element.side_effect = [False] * 30 + [True]
    mock_auto.find_element.side_effect = RuntimeError("recognition failed")
    mirror = object.__new__(Mirror)

    assert mirror.acquire_ego_gift() is None

    assert mock_wait.call_count == 31
    assert mock_auto.click_element.call_count == 31
    assert mock_auto.find_element.call_count == 30
