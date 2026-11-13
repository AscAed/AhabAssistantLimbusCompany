from unittest.mock import patch

import pytest

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
