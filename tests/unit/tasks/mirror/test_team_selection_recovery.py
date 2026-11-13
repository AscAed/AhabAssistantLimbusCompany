from unittest.mock import patch

import pytest

from tasks.mirror.mirror import Mirror


@patch(
    "tasks.mirror.mirror.wait_for_screenshot",
    side_effect=RuntimeError("等待截图超时"),
)
@patch("tasks.mirror.mirror.select_battle_team", return_value=True)
@patch("tasks.mirror.mirror.auto")
@patch("tasks.mirror.mirror.cfg")
def test_select_mirror_team_stops_after_bounded_capture_failure(
    mock_cfg, mock_auto, _select_team, mock_wait_for_screenshot
):
    mock_cfg.config.teams = {}
    mock_auto.find_element.return_value = None
    mock_auto.take_screenshot.side_effect = [
        None,
        AssertionError("unbounded screenshot retry"),
    ]
    mirror = object.__new__(Mirror)
    mirror.team_number = 1
    mirror.team_order = 1

    with pytest.raises(RuntimeError, match="等待截图超时"):
        mirror.select_mirror_team()

    mock_wait_for_screenshot.assert_called_once_with()
    mock_auto.take_screenshot.assert_not_called()
    mock_auto.click_element.assert_not_called()
