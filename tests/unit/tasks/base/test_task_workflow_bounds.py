from types import SimpleNamespace
from unittest.mock import Mock, patch

from tasks.base import script_task_scheme
from tasks.base.back_init_menu import back_init_menu
from tasks.base.retry import restart_game
from tasks.base.task_engine import BuyEnkephalinTask, GetRewardTask, MirrorDungeonTask
from tasks.daily.get_prize import get_mail_prize, get_pass_prize
from tasks.daily.luxcavation import EXP_luxcavation, thread_luxcavation


def _mirror_task_config(mirror_count=1, re_claim_rewards=False):
    team_setting = SimpleNamespace(fixed_team_use=False, fixed_team_use_select=0)
    return SimpleNamespace(
        set_mirror_count=mirror_count,
        infinite_dungeons=False,
        save_rewards=False,
        hard_mirror=False,
        auto_hard_mirror=False,
        teams_active_queue=[1],
        re_claim_rewards=re_claim_rewards,
        config=SimpleNamespace(teams={"1": team_setting}),
        get_value=Mock(return_value=[True]),
        normalize_and_sync_team_state=Mock(),
        rotate_team_queue=Mock(),
        set_value=Mock(),
    )


def test_mirror_task_stops_after_three_consecutive_dungeon_failures():
    cfg = _mirror_task_config()
    mediator = SimpleNamespace(
        mirror_signal=SimpleNamespace(emit=Mock()),
        mirror_bar_kill_signal=SimpleNamespace(emit=Mock()),
    )
    with patch.object(script_task_scheme, "cfg", cfg), patch.object(
        script_task_scheme, "mediator", mediator
    ), patch.object(
        script_task_scheme,
        "onetime_mir_process",
        side_effect=[False, False, False, True],
    ) as run_once:
        result = script_task_scheme.Mirror_task()

    assert result is False
    assert run_once.call_count == 3
    mediator.mirror_bar_kill_signal.emit.assert_called_once_with()


def test_mirror_task_resets_failure_streak_after_a_success():
    cfg = _mirror_task_config(mirror_count=2)
    mediator = SimpleNamespace(
        mirror_signal=SimpleNamespace(emit=Mock()),
        mirror_bar_kill_signal=SimpleNamespace(emit=Mock()),
    )
    with patch.object(script_task_scheme, "cfg", cfg), patch.object(
        script_task_scheme, "mediator", mediator
    ), patch.object(
        script_task_scheme,
        "onetime_mir_process",
        side_effect=[False, False, True, False, False, True],
    ) as run_once:
        result = script_task_scheme.Mirror_task()

    assert result is True
    assert run_once.call_count == 6
    assert mediator.mirror_signal.emit.call_count == 3


def test_mirror_task_propagates_reward_claim_failure():
    cfg = _mirror_task_config(re_claim_rewards=True)
    mediator = SimpleNamespace(
        mirror_signal=SimpleNamespace(emit=Mock()),
        mirror_bar_kill_signal=SimpleNamespace(emit=Mock()),
    )
    with patch.object(script_task_scheme, "cfg", cfg), patch.object(
        script_task_scheme, "mediator", mediator
    ), patch.object(
        script_task_scheme, "onetime_mir_process", return_value=True
    ) as run_once, patch.object(
        script_task_scheme, "to_get_reward", return_value=False
    ):
        result = script_task_scheme.Mirror_task()

    assert result is False
    run_once.assert_called_once()
    mediator.mirror_bar_kill_signal.emit.assert_called_once_with()


def test_mirror_task_counts_completed_run_when_menu_recovery_fails():
    cfg = _mirror_task_config(mirror_count=1)
    cfg.hard_mirror = True
    cfg.auto_hard_mirror = True
    cfg.hard_mirror_chance = 2
    mediator = SimpleNamespace(
        mirror_signal=SimpleNamespace(emit=Mock()),
        mirror_bar_kill_signal=SimpleNamespace(emit=Mock()),
    )
    with patch.object(script_task_scheme, "cfg", cfg), patch.object(
        script_task_scheme, "mediator", mediator
    ), patch.object(
        script_task_scheme,
        "onetime_mir_process",
        side_effect=[
            script_task_scheme.MirrorRunOutcome.COMPLETED_RECOVERY_FAILED,
            True,
        ],
    ) as run_once:
        result = script_task_scheme.Mirror_task()

    assert result is False
    run_once.assert_called_once()
    assert mediator.mirror_signal.emit.call_args_list == [
        ((0, 1),),
        ((1, 0),),
    ]
    cfg.set_value.assert_called_once_with("hard_mirror_chance", 1)
    mediator.mirror_bar_kill_signal.emit.assert_called_once_with()


def test_mirror_task_failure_reaches_task_engine_contract():
    engine = SimpleNamespace(thread=None)
    with patch(
        "tasks.base.script_task_scheme.Mirror_task", return_value=False
    ):
        assert MirrorDungeonTask().run(engine) is False


def test_main_menu_recovery_stops_after_three_restart_attempts():
    with patch("tasks.base.back_init_menu.auto") as mock_auto, patch(
        "tasks.base.back_init_menu.ensure_simulator_game_started",
        return_value=False,
    ), patch("tasks.base.back_init_menu.retry", return_value=None), patch(
        "tasks.base.back_init_menu.update_model_for_retry"
    ), patch("tasks.base.back_init_menu.sleep"), patch(
        "tasks.base.retry.kill_game"
    ) as kill_game, patch(
        "tasks.base.script_task_scheme.init_game"
    ) as init_game, patch("tasks.base.retry.sleep"):
        mock_auto.click_element.return_value = False
        mock_auto.find_element.return_value = False

        result = back_init_menu()

    assert result is False
    assert kill_game.call_count == 3
    assert init_game.call_count == 3


def test_maintenance_recovery_stops_after_three_restart_attempts():
    with patch("tasks.base.back_init_menu.auto") as mock_auto, patch(
        "tasks.base.back_init_menu.ensure_simulator_game_started",
        return_value=False,
    ), patch("tasks.base.back_init_menu.retry", return_value=None), patch(
        "tasks.base.back_init_menu.update_model_for_retry"
    ), patch("tasks.base.retry.kill_game") as kill_game, patch(
        "tasks.base.script_task_scheme.init_game"
    ) as init_game, patch("tasks.base.retry.sleep"), patch(
        "utils.utils.get_day_of_week", return_value=1
    ):
        mock_auto.click_element.return_value = False
        mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (
            target == "base/notification_close_assets.png"
        )

        result = back_init_menu()

    assert result is False
    assert kill_game.call_count == 3
    assert init_game.call_count == 3


def test_restart_game_uses_non_restarting_menu_recovery():
    with patch("tasks.base.script_task_scheme.init_game"), patch(
        "tasks.base.retry.sleep"
    ), patch(
        "tasks.base.back_init_menu.back_init_menu", return_value=False
    ) as recover_menu:
        assert restart_game() is False

    recover_menu.assert_called_once_with(allow_restart=False)


def test_main_menu_recovery_returns_after_successful_navigation():
    with patch("tasks.base.back_init_menu.auto") as mock_auto, patch(
        "tasks.base.back_init_menu.ensure_simulator_game_started",
        return_value=False,
    ), patch("tasks.base.back_init_menu.retry", return_value=None):
        mock_auto.click_element.side_effect = lambda target, *args, **kwargs: (
            target == "home/window_assets.png"
        )
        mock_auto.find_element.return_value = True

        assert back_init_menu() is True


def test_pass_reward_navigation_stops_after_repeated_mission_clicks():
    click_count = 0

    def click(target, *args, **kwargs):
        nonlocal click_count
        if target != "pass/pass_missions_assets.png":
            return False
        click_count += 1
        if click_count > 31:
            raise AssertionError("pass navigation exceeded its iteration bound")
        return True

    with patch("tasks.daily.get_prize.wait_for_screenshot"), patch(
        "tasks.daily.get_prize.auto"
    ) as mock_auto:
        mock_auto.find_element.return_value = None
        mock_auto.click_element.side_effect = click

        result = get_pass_prize()

    assert result is False
    assert click_count == 31


def test_mail_reward_navigation_stops_after_repeated_mail_clicks():
    click_count = 0

    def click(target, *args, **kwargs):
        nonlocal click_count
        if target != "home/mail_assets.png":
            return False
        click_count += 1
        if click_count > 31:
            raise AssertionError("mail navigation exceeded its iteration bound")
        return True

    with patch("tasks.daily.get_prize.wait_for_screenshot"), patch(
        "tasks.daily.get_prize.retry", return_value=None
    ), patch("tasks.daily.get_prize.auto") as mock_auto:
        mock_auto.click_element.side_effect = click

        result = get_mail_prize()

    assert result is False
    assert click_count == 31


def test_pass_reward_returns_success_after_daily_and_weekly_claims():
    with patch("tasks.daily.get_prize.wait_for_screenshot"), patch(
        "tasks.daily.get_prize.retry", return_value=None
    ), patch("tasks.daily.get_prize.auto") as mock_auto:
        mock_auto.find_element.side_effect = [[(10, 20)], [(30, 40)]]

        assert get_pass_prize() is True

    assert mock_auto.mouse_click.call_args_list == [
        ((10, 20),),
        ((30, 40),),
    ]
    assert mock_auto.click_element.call_args_list == [
        (("pass/weekly_assets.png",), {})
    ]


def test_pass_reward_returns_success_when_daily_and_weekly_pages_have_no_claims():
    def find(target, *args, **kwargs):
        if target == "pass/pass_coin.png":
            return None
        return target in {
            "pass/pass_missions_assets.png",
            "pass/weekly_assets.png",
        }

    def click(target, *args, **kwargs):
        return target in {
            "pass/pass_missions_assets.png",
            "pass/weekly_assets.png",
        }

    with patch("tasks.daily.get_prize.wait_for_screenshot"), patch(
        "tasks.daily.get_prize.auto"
    ) as mock_auto:
        mock_auto.find_element.side_effect = find
        mock_auto.click_element.side_effect = click

        assert get_pass_prize() is True


def test_mail_reward_returns_success_after_confirmation():
    with patch("tasks.daily.get_prize.wait_for_screenshot"), patch(
        "tasks.daily.get_prize.retry", return_value=None
    ), patch("tasks.daily.get_prize.auto") as mock_auto:
        mock_auto.click_element.side_effect = lambda target, *args, **kwargs: (
            target == "mail/get_mail_prize_confirm.png"
            or target == "mail/close_assets.png"
        )

        assert get_mail_prize() is True

    assert mock_auto.click_element.call_args_list == [
        (("mail/get_mail_prize_confirm.png",), {}),
        (("mail/close_assets.png",), {}),
    ]


def test_experience_dungeon_navigation_stops_after_repeated_entry_clicks():
    click_count = 0

    def click(target, *args, **kwargs):
        nonlocal click_count
        if target != "home/luxcavation_assets.png":
            return False
        click_count += 1
        if click_count > 31:
            raise AssertionError("experience navigation exceeded its iteration bound")
        return True

    with patch("tasks.daily.luxcavation.wait_for_screenshot"), patch(
        "tasks.daily.luxcavation.auto"
    ) as mock_auto:
        mock_auto.find_element.return_value = None
        mock_auto.click_element.side_effect = click

        result = EXP_luxcavation()

    assert result is False
    assert click_count == 31


def test_thread_dungeon_navigation_stops_after_repeated_entry_clicks():
    click_count = 0

    def click(target, *args, **kwargs):
        nonlocal click_count
        if target != "home/luxcavation_assets.png":
            return False
        click_count += 1
        if click_count > 31:
            raise AssertionError("thread navigation exceeded its iteration bound")
        return True

    with patch("tasks.daily.luxcavation.wait_for_screenshot"), patch(
        "tasks.daily.luxcavation.auto"
    ) as mock_auto:
        mock_auto.find_element.return_value = None
        mock_auto.click_element.side_effect = click

        result = thread_luxcavation()

    assert result is False
    assert click_count == 31


def test_experience_dungeon_navigation_returns_on_team_screen():
    with patch("tasks.daily.luxcavation.wait_for_screenshot"), patch(
        "tasks.daily.luxcavation.auto"
    ) as mock_auto:
        mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (
            target == "teams/identify_assets.png"
        )

        assert EXP_luxcavation() is True


def test_thread_dungeon_navigation_returns_on_team_screen():
    with patch("tasks.daily.luxcavation.wait_for_screenshot"), patch(
        "tasks.daily.luxcavation.auto"
    ) as mock_auto:
        mock_auto.find_element.side_effect = lambda target, *args, **kwargs: (
            target == "teams/identify_assets.png"
        )

        assert thread_luxcavation() is True


def test_reward_wrapper_stops_after_pass_claim_failure():
    with patch.object(script_task_scheme, "cfg") as cfg, patch.object(
        script_task_scheme, "back_init_menu", return_value=True
    ) as back_to_menu, patch.object(
        script_task_scheme, "get_pass_prize", return_value=False
    ) as get_pass:
        cfg.set_get_prize = 1

        assert script_task_scheme.to_get_reward() is False

    back_to_menu.assert_called_once_with()
    get_pass.assert_called_once_with()


def test_reward_wrapper_stops_after_mail_claim_failure():
    with patch.object(script_task_scheme, "cfg") as cfg, patch.object(
        script_task_scheme, "back_init_menu", return_value=True
    ) as back_to_menu, patch.object(
        script_task_scheme, "get_mail_prize", return_value=False
    ) as get_mail:
        cfg.set_get_prize = 2

        assert script_task_scheme.to_get_reward() is False

    back_to_menu.assert_called_once_with()
    get_mail.assert_called_once_with()


def test_reward_wrapper_stops_when_menu_recovery_fails():
    with patch.object(script_task_scheme, "cfg") as cfg, patch.object(
        script_task_scheme, "back_init_menu", return_value=False
    ) as back_to_menu, patch.object(
        script_task_scheme, "get_mail_prize"
    ) as get_mail:
        cfg.set_get_prize = 2

        assert script_task_scheme.to_get_reward() is False

    back_to_menu.assert_called_once_with()
    get_mail.assert_not_called()


def test_get_reward_task_propagates_failure_to_task_engine():
    engine = SimpleNamespace()
    with patch(
        "tasks.base.script_task_scheme.to_get_reward", return_value=False
    ):
        assert GetRewardTask().run(engine) is False


def test_experience_task_stops_when_post_battle_menu_recovery_fails():
    with patch.object(
        script_task_scheme,
        "cfg",
        SimpleNamespace(targeted_teaming_EXP=False, daily_teams=1),
    ), patch.object(
        script_task_scheme, "EXP_luxcavation", return_value=True
    ), patch.object(
        script_task_scheme, "select_battle_team", return_value=True
    ), patch.object(
        script_task_scheme.battle, "to_battle", return_value=True
    ), patch.object(
        script_task_scheme.battle, "fight"
    ), patch.object(
        script_task_scheme, "back_init_menu", return_value=False
    ), patch.object(
        script_task_scheme, "make_enkephalin_module"
    ) as make_enkephalin:
        assert script_task_scheme.onetime_EXP_process() is False

    make_enkephalin.assert_not_called()


def test_thread_task_stops_when_post_battle_menu_recovery_fails():
    with patch.object(
        script_task_scheme,
        "cfg",
        SimpleNamespace(targeted_teaming_thread=False, daily_teams=1),
    ), patch.object(
        script_task_scheme, "thread_luxcavation", return_value=True
    ), patch.object(
        script_task_scheme, "select_battle_team", return_value=True
    ), patch.object(
        script_task_scheme.battle, "to_battle", return_value=True
    ), patch.object(
        script_task_scheme.battle, "fight"
    ), patch.object(
        script_task_scheme, "back_init_menu", return_value=False
    ), patch.object(
        script_task_scheme, "make_enkephalin_module"
    ) as make_enkephalin:
        assert script_task_scheme.onetime_thread_process() is False

    make_enkephalin.assert_not_called()


def test_mirror_task_stops_when_post_run_menu_recovery_fails():
    with patch.object(
        script_task_scheme,
        "cfg",
        SimpleNamespace(auto_hard_mirror=False),
    ), patch.object(
        script_task_scheme, "Mirror"
    ) as mirror, patch.object(
        script_task_scheme, "back_init_menu", return_value=False
    ), patch.object(
        script_task_scheme, "make_enkephalin_module"
    ) as make_enkephalin:
        mirror.return_value.run.return_value = True

        assert (
            script_task_scheme.onetime_mir_process(SimpleNamespace(), 1)
            is script_task_scheme.MirrorRunOutcome.COMPLETED_RECOVERY_FAILED
        )

    make_enkephalin.assert_not_called()


def test_daily_task_stops_when_initial_menu_recovery_fails():
    with patch.object(
        script_task_scheme, "back_init_menu", return_value=False
    ), patch.object(
        script_task_scheme, "make_enkephalin_module"
    ) as make_enkephalin:
        run_daily = script_task_scheme.Daily_task_wrapper()

        assert run_daily() is False

    make_enkephalin.assert_not_called()


def test_buy_enkephalin_task_propagates_menu_recovery_failure():
    with patch.object(
        script_task_scheme,
        "cfg",
        SimpleNamespace(set_lunacy_to_enkephalin=2),
    ), patch.object(
        script_task_scheme, "back_init_menu", return_value=False
    ), patch.object(
        script_task_scheme, "lunacy_to_enkephalin"
    ) as buy_enkephalin:
        assert BuyEnkephalinTask().run(SimpleNamespace()) is False

    buy_enkephalin.assert_not_called()


def test_experience_navigation_stops_when_menu_recovery_fails():
    def find(target, *args, **kwargs):
        return target in {
            "home/luxcavation_assets.png",
            "home/inferno_bus_assets.png",
            "base/renew_confirm_assets.png",
            "home/drive_assets.png",
        }

    with patch("tasks.daily.luxcavation.wait_for_screenshot"), patch(
        "tasks.daily.luxcavation.auto"
    ) as mock_auto, patch(
        "tasks.base.back_init_menu.back_init_menu", return_value=False
    ) as back_to_menu:
        mock_auto.find_element.side_effect = find
        mock_auto.click_element.side_effect = lambda target, *args, **kwargs: (
            target == "base/renew_confirm_assets.png"
        )

        assert EXP_luxcavation() is False

    back_to_menu.assert_called_once_with()


def test_thread_navigation_stops_when_menu_recovery_fails():
    def find(target, *args, **kwargs):
        return target in {
            "home/luxcavation_assets.png",
            "home/inferno_bus_assets.png",
            "base/renew_confirm_assets.png",
            "home/drive_assets.png",
        }

    with patch("tasks.daily.luxcavation.wait_for_screenshot"), patch(
        "tasks.daily.luxcavation.auto"
    ) as mock_auto, patch(
        "tasks.base.back_init_menu.back_init_menu", return_value=False
    ) as back_to_menu:
        mock_auto.find_element.side_effect = find
        mock_auto.click_element.side_effect = lambda target, *args, **kwargs: (
            target == "base/renew_confirm_assets.png"
        )

        assert thread_luxcavation() is False

    back_to_menu.assert_called_once_with()
