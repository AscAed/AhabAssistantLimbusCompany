from unittest.mock import call, patch

from PIL import Image, ImageDraw

from tasks.teams.team_formation import clean_team, load_team_code_in_game, select_battle_team, team_formation


def _frame_with_team_list(changed: bool = False) -> Image.Image:
    frame = Image.new("L", (2560, 1440), 0)
    if changed:
        ImageDraw.Draw(frame).rectangle((120, 500, 240, 620), fill=255)
    return frame


def _frame_with_fixed_ui_change() -> Image.Image:
    frame = _frame_with_team_list()
    ImageDraw.Draw(frame).rectangle((1000, 100, 1100, 200), fill=255)
    return frame


def _team_selection_auto(mock_auto) -> dict[str, str]:
    state = {"value": "unknown"}

    def find_element(target, *args, **kwargs):
        if kwargs.get("take_screenshot"):
            mock_auto.take_screenshot()
        if target == "teams/identify_assets.png":
            return 2300, 200
        return None

    def report_background_input_result(success: bool) -> None:
        if success:
            if state["value"] != "fallback_visible":
                state["value"] = "supported"
        else:
            state["value"] = "fallback_visible"

    mock_auto.find_element.side_effect = find_element
    mock_auto.find_language_text.return_value = None
    mock_auto.get_background_input_state.side_effect = lambda: state["value"]
    mock_auto.report_background_input_result.side_effect = report_background_input_result
    mock_auto.batch_mouse_scroll.return_value = True
    mock_auto.mouse_drag.return_value = True
    return state


def test_team_selection_initial_screenshot_timeout_stops():
    with patch("tasks.teams.team_formation.auto") as mock_auto, patch(
        "tasks.teams.team_formation.cfg"
    ) as mock_cfg:
        mock_cfg.set_win_size = 1440
        mock_auto.take_screenshot.side_effect = [None, None, None, AssertionError("unbounded capture")]

        assert select_battle_team(1) is False

    assert mock_auto.take_screenshot.call_count == 3
    mock_auto.find_element.assert_not_called()


def test_team_selection_stops_when_team_anchor_is_missing():
    with patch("tasks.teams.team_formation.auto") as mock_auto, patch(
        "tasks.teams.team_formation.cfg"
    ) as mock_cfg:
        mock_cfg.set_win_size = 1440
        mock_auto.take_screenshot.return_value = _frame_with_team_list()
        mock_auto.find_element.return_value = None

        assert select_battle_team(1) is False

    mock_auto.mouse_click.assert_not_called()
    mock_auto.batch_mouse_scroll.assert_not_called()
    mock_auto.mouse_drag.assert_not_called()


def test_clean_team_returns_false_after_bounded_attempts():
    frames = [_frame_with_team_list()] * 30 + [AssertionError("unbounded clean loop")]
    with patch("tasks.teams.team_formation.auto") as mock_auto, patch(
        "tasks.teams.team_formation.cfg"
    ) as mock_cfg, patch("tasks.teams.team_formation.sleep"):
        mock_cfg.set_win_size = 1440
        mock_auto.take_screenshot.side_effect = frames
        mock_auto.click_element.return_value = False
        mock_auto.find_element.return_value = None

        assert clean_team() is False

    assert mock_auto.take_screenshot.call_count == 30


def test_team_formation_stops_when_clean_team_fails():
    with patch("tasks.teams.team_formation.clean_team", return_value=False), patch(
        "tasks.teams.team_formation.auto"
    ) as mock_auto, patch("tasks.teams.team_formation.cfg") as mock_cfg:
        mock_cfg.set_win_size = 1440

        assert team_formation([1, 2, 3, 4, 5]) is False

    mock_auto.take_screenshot.assert_not_called()
    mock_auto.mouse_click.assert_not_called()


def test_team_formation_accepts_partial_sinner_selection():
    with patch("tasks.teams.team_formation.clean_team", return_value=True), patch(
        "tasks.teams.team_formation._capture_screenshot_with_retries",
        return_value=_frame_with_team_list(),
    ), patch("tasks.teams.team_formation.auto") as mock_auto, patch(
        "tasks.teams.team_formation.cfg"
    ) as mock_cfg, patch("tasks.teams.team_formation.sleep"):
        mock_cfg.set_win_size = 1440
        mock_cfg.mouse_action_interval = 0
        mock_auto.find_element.return_value = (2300, 200)

        assert team_formation([1, 4, 7]) is True

    assert mock_auto.mouse_click.call_count == 3


def test_team_formation_rejects_empty_sinner_selection():
    with patch("tasks.teams.team_formation.clean_team") as clean_team_mock:
        assert team_formation([0] * 12) is False

    clean_team_mock.assert_not_called()


def test_load_team_code_capture_failure_stops():
    with patch("tasks.teams.team_formation.auto") as mock_auto, patch(
        "tasks.teams.team_formation.sleep"
    ):
        mock_auto.find_element.return_value = True
        mock_auto.take_screenshot.side_effect = [None, None, None, AssertionError("unbounded capture")]

        assert load_team_code_in_game("test-code") is False

    assert mock_auto.take_screenshot.call_count == 3


def test_team_selection_scroll_verification_uses_visible_fallback():
    same_frame = _frame_with_team_list()
    changed_frame = _frame_with_team_list(changed=True)
    state = None
    with patch("tasks.teams.team_formation.auto") as mock_auto, patch(
        "tasks.teams.team_formation.cfg"
    ) as mock_cfg, patch("tasks.teams.team_formation.sleep"):
        mock_cfg.set_win_size = 1440
        mock_cfg.select_team_by_order = True
        state = _team_selection_auto(mock_auto)
        mock_auto.find_language_text.side_effect = [None, (150, 635)]
        mock_auto.take_screenshot.side_effect = [
            same_frame,
            same_frame,
            same_frame,
            same_frame,
            changed_frame,
        ]

        assert select_battle_team(1) is True

    mock_auto.batch_mouse_scroll.assert_called_once()
    mock_auto.mouse_drag.assert_called_once()
    assert state["value"] == "fallback_visible"
    assert mock_auto.report_background_input_result.call_args_list == [call(False)]


def test_team_selection_at_top_without_movement_is_accepted():
    frame = _frame_with_team_list()
    state = None
    with patch("tasks.teams.team_formation.auto") as mock_auto, patch(
        "tasks.teams.team_formation.cfg"
    ) as mock_cfg, patch("tasks.teams.team_formation.sleep"):
        mock_cfg.set_win_size = 1440
        mock_cfg.select_team_by_order = True
        state = _team_selection_auto(mock_auto)
        mock_auto.take_screenshot.return_value = frame
        mock_auto.find_language_text.return_value = (150, 635)

        assert select_battle_team(1) is True

    assert state["value"] == "unknown"
    mock_auto.mouse_drag.assert_not_called()
    mock_auto.report_background_input_result.assert_not_called()


def test_team_selection_no_observable_scroll_stops():
    frame = _frame_with_team_list()
    with patch("tasks.teams.team_formation.auto") as mock_auto, patch(
        "tasks.teams.team_formation.cfg"
    ) as mock_cfg, patch("tasks.teams.team_formation.sleep"):
        mock_cfg.set_win_size = 1440
        mock_cfg.select_team_by_order = True
        state = _team_selection_auto(mock_auto)
        mock_auto.take_screenshot.return_value = frame

        assert select_battle_team(1) is False

    assert state["value"] == "fallback_visible"
    mock_auto.mouse_drag.assert_called_once()
    assert call(1, 1) in mock_auto.mouse_click.call_args_list
    assert call(150.0, 485.0) not in mock_auto.mouse_click.call_args_list

def test_team_selection_ignores_changes_outside_scroll_pane():
    base_frame = _frame_with_team_list()
    fixed_ui_change = _frame_with_fixed_ui_change()
    with patch("tasks.teams.team_formation.auto") as mock_auto, patch(
        "tasks.teams.team_formation.cfg"
    ) as mock_cfg, patch("tasks.teams.team_formation.sleep"):
        mock_cfg.set_win_size = 1440
        mock_cfg.select_team_by_order = True
        state = _team_selection_auto(mock_auto)
        mock_auto.take_screenshot.side_effect = [
            base_frame,
            base_frame,
            base_frame,
            fixed_ui_change,
            base_frame,
        ]

        assert select_battle_team(1) is False

    assert state["value"] == "fallback_visible"
    assert call(1, 1) in mock_auto.mouse_click.call_args_list
    assert call(150.0, 485.0) not in mock_auto.mouse_click.call_args_list


def test_team_selection_uses_single_scroll_when_batch_scroll_unavailable():
    frame = _frame_with_team_list()
    with patch("tasks.teams.team_formation.auto") as mock_auto, patch(
        "tasks.teams.team_formation.cfg"
    ) as mock_cfg, patch("tasks.teams.team_formation.sleep"):
        mock_cfg.set_win_size = 1440
        mock_cfg.select_team_by_order = True
        _team_selection_auto(mock_auto)
        mock_auto.batch_mouse_scroll = None
        mock_auto.take_screenshot.return_value = frame
        mock_auto.find_language_text.return_value = (150, 635)
        mock_auto.mouse_scroll.return_value = True

        assert select_battle_team(1) is True

    assert mock_auto.mouse_scroll.call_count == 30
    assert mock_auto.mouse_scroll.call_args_list == [call(1, 150, 635)] * 30
    mock_auto.mouse_drag.assert_not_called()
    mock_auto.report_background_input_result.assert_not_called()
