from types import SimpleNamespace
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


@patch("tasks.mirror.mirror.time.sleep")
@patch("tasks.mirror.mirror.load_team_code_in_game", return_value=False)
@patch("tasks.mirror.mirror.select_battle_team", return_value=True)
@patch("tasks.mirror.mirror.auto")
@patch("tasks.mirror.mirror.cfg")
def test_select_mirror_team_continues_after_team_code_load_failure(
    mock_cfg, mock_auto, mock_select_team, mock_load_team_code, _sleep
):
    mock_cfg.config.teams = {
        "1": SimpleNamespace(use_team_code=True, team_code="test-code")
    }
    mock_auto.find_element.return_value = True
    mirror = object.__new__(Mirror)
    mirror.team_number = 1
    mirror.team_order = 1

    assert mirror.select_mirror_team() is True

    mock_select_team.assert_called_once_with(1)
    mock_load_team_code.assert_called_once_with("test-code")
    mock_auto.find_element.assert_called_once_with(
        "mirror/road_to_mir/dreaming_star/coins_assets.png"
    )
    _sleep.assert_called_once_with(3)


def test_select_mirror_team_returns_false_after_entry_attempts_are_exhausted():
    with (
        patch("tasks.mirror.mirror.back_init_menu") as mock_back_init_menu,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
        patch("tasks.mirror.mirror.retry", return_value=True),
        patch("tasks.mirror.mirror.select_battle_team", return_value=True),
        patch("tasks.mirror.mirror.time.sleep"),
        patch("tasks.mirror.mirror.wait_for_screenshot") as mock_wait_for_screenshot,
    ):
        mock_cfg.config.teams = {}
        mock_auto.click_element.return_value = False
        mock_auto.find_element.return_value = None
        mock_auto.find_language_text.return_value = False
        mirror = object.__new__(Mirror)
        mirror.team_number = 1
        mirror.team_order = 1

        assert mirror.select_mirror_team() is False

    mock_back_init_menu.assert_called_once_with()
    assert mock_wait_for_screenshot.call_count == 31
