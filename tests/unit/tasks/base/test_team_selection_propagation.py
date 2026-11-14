from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from module.automation.automation import GameState
from module.my_error.my_error import unableToFindTeamError
from tasks.base import script_task_scheme
from tasks.base.task_engine import DailyLuxcavationTask
from tasks.mirror.mirror import Mirror


def test_experience_run_stops_when_team_selection_fails():
    with patch.object(script_task_scheme, "cfg") as cfg, patch.object(
        script_task_scheme, "EXP_luxcavation"
    ) as experience, patch.object(
        script_task_scheme, "select_battle_team", return_value=False
    ) as select_team, patch.object(
        script_task_scheme.battle, "to_battle"
    ) as enter_battle, patch.object(
        script_task_scheme.battle, "fight"
    ) as fight, patch.object(
        script_task_scheme, "back_init_menu"
    ), patch.object(
        script_task_scheme, "make_enkephalin_module"
    ):
        cfg.targeted_teaming_EXP = False
        cfg.daily_teams = 3

        assert script_task_scheme.onetime_EXP_process() is False

    experience.assert_called_once_with(1)
    select_team.assert_called_once_with(3)
    enter_battle.assert_not_called()
    fight.assert_not_called()


def test_thread_run_stops_when_team_selection_fails():
    with patch.object(script_task_scheme, "cfg") as cfg, patch.object(
        script_task_scheme, "thread_luxcavation"
    ) as thread, patch.object(
        script_task_scheme, "select_battle_team", return_value=False
    ) as select_team, patch.object(
        script_task_scheme.battle, "to_battle"
    ) as enter_battle, patch.object(
        script_task_scheme.battle, "fight"
    ) as fight, patch.object(
        script_task_scheme, "back_init_menu"
    ), patch.object(
        script_task_scheme, "make_enkephalin_module"
    ):
        cfg.targeted_teaming_thread = False
        cfg.daily_teams = 4

        assert script_task_scheme.onetime_thread_process() is False

    thread.assert_called_once_with(1)
    select_team.assert_called_once_with(4)
    enter_battle.assert_not_called()
    fight.assert_not_called()


def test_single_combat_run_stops_after_a_failed_experience_run():
    with patch.object(
        script_task_scheme, "onetime_EXP_process", return_value=False
    ) as experience, patch.object(
        script_task_scheme, "onetime_thread_process"
    ) as thread:
        assert script_task_scheme._single_combat_run(2, 1) is False

    experience.assert_called_once_with()
    thread.assert_not_called()


def test_batch_combat_stops_after_a_failed_batch():
    process = Mock(side_effect=[False, True, True])

    assert script_task_scheme._batch_combat(process, times=5, max_times=2) is False

    process.assert_called_once_with(2)


def test_daily_task_reports_wrapper_failure():
    engine = SimpleNamespace(get_reward_context=None)
    with patch(
        "tasks.base.script_task_scheme.Daily_task_wrapper",
        return_value=lambda: False,
    ):
        assert DailyLuxcavationTask().run(engine) is False


def test_mirror_stops_when_initial_formation_fails():
    mirror = object.__new__(Mirror)
    mirror.first_battle = True
    mirror.sinner_team = [1, 2, 3]
    mirror.LOOP_COUNT = 1000
    dispatcher = Mock()
    dispatcher.detect_state.side_effect = [
        GameState.BATTLE_FORMATION,
        AssertionError("Mirror advanced after a failed formation"),
    ]

    with patch("tasks.mirror.mirror.PageStateDispatcher", return_value=dispatcher), patch(
        "tasks.mirror.mirror.auto"
    ) as auto, patch("tasks.mirror.in_shop.auto") as screenshot_auto, patch(
        "tasks.mirror.mirror.cfg"
    ) as cfg, patch(
        "tasks.mirror.mirror.retry"
    ), patch("tasks.mirror.mirror.team_formation", return_value=False):
        cfg.floor_3_exit = False
        auto.click_element.return_value = False
        auto.find_element.return_value = False
        screenshot_auto.take_screenshot.return_value = object()
        with patch.object(mirror, "check_and_recover_process", return_value=False):
            with pytest.raises(unableToFindTeamError):
                mirror.run()


def test_onetime_mirror_propagates_team_selection_failure():
    failure = unableToFindTeamError("team selection failed")
    with patch.object(script_task_scheme, "cfg") as cfg, patch.object(
        script_task_scheme, "Mirror"
    ) as mirror_type:
        cfg.auto_hard_mirror = False
        mirror_type.return_value.run.side_effect = failure

        with pytest.raises(unableToFindTeamError) as raised:
            script_task_scheme.onetime_mir_process(Mock(), 1)

    assert raised.value is failure
