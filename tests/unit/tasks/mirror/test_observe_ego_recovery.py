from unittest.mock import patch

from tasks.mirror.mirror import GameState, Mirror


def test_select_observe_ego_gift_returns_false_when_benchmark_is_missing():
    with (
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
    ):
        mock_cfg.set_win_size = 1440
        mock_auto.find_element.return_value = None

        mirror = object.__new__(Mirror)
        mirror.observe_ego_gift_selected = []

        assert mirror.select_observe_ego_gift() is False


def test_select_observe_ego_gift_returns_false_after_transition_budget():
    with (
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
        patch("tasks.mirror.mirror.ImageUtils") as mock_image_utils,
        patch("tasks.mirror.mirror.sleep"),
    ):
        mock_cfg.set_win_size = 1440
        mock_auto.find_element.side_effect = (
            lambda target, *args, **kwargs: (200, 100)
            if "observe_burn_assets.png" in target
            else None
        )
        mock_auto.take_screenshot.return_value = object()
        mock_auto.find_language_text.return_value = None
        mock_auto.click_element.return_value = False
        mock_image_utils.get_bbox.return_value = [100, 200, 1200, 1000]

        mirror = object.__new__(Mirror)
        mirror.observe_ego_gift_selected = []

        assert mirror.select_observe_ego_gift() is False
        assert mock_auto.take_screenshot.call_count == 5


def test_mirror_run_stops_when_observe_ego_selection_fails():
    with (
        patch("tasks.mirror.mirror.PageStateDispatcher") as dispatcher_type,
        patch("tasks.mirror.mirror.auto") as mock_auto,
        patch("tasks.mirror.mirror.cfg") as mock_cfg,
        patch("tasks.mirror.mirror.battle") as mock_battle,
        patch("tasks.mirror.mirror.wait_for_screenshot"),
        patch("tasks.mirror.mirror.retry", return_value=True),
    ):
        dispatcher_type.return_value.detect_state.return_value = GameState.UNKNOWN
        mock_cfg.floor_3_exit = False
        mock_battle.fail_times = 0
        mock_auto.click_element.return_value = False
        mock_auto.find_language_text.return_value = False
        mock_auto.find_element.side_effect = (
            lambda target, *args, **kwargs: "observe_burn_assets.png" in target
        )

        mirror = object.__new__(Mirror)
        mirror.LOOP_COUNT = 1
        mirror.check_and_recover_process = lambda: False
        mirror.floor = 0
        mirror.get_floor_num = False
        mirror.first_battle = False
        mirror.observe_ego_gift_selected = []
        mirror.select_observe_ego_gift = lambda: False

        assert mirror.run() is False
