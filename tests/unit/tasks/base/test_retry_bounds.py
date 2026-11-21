from importlib import import_module
from unittest.mock import Mock, patch

retry_module = import_module("tasks.base.retry")


def test_retry_limits_simulator_start_attempts_before_timing_out():
    attempts = 0

    def start_simulator_game():
        nonlocal attempts
        attempts += 1
        if attempts > 3:
            raise AssertionError("simulator start attempts were not bounded")
        return True

    mocked_config = Mock()
    mocked_config.config.simulator = True
    mocked_automation = Mock()
    mocked_automation.get_restore_time.return_value = None

    with (
        patch.object(retry_module, "cfg", mocked_config),
        patch.object(retry_module, "auto", mocked_automation),
        patch.object(
            retry_module,
            "ensure_simulator_game_started",
            side_effect=start_simulator_game,
        ),
        patch.object(retry_module, "check_times", return_value=True) as check_times,
        patch.object(retry_module.time, "time", return_value=123.0),
    ):
        assert retry_module.retry() is False

    assert attempts == 3
    check_times.assert_called_once_with(123.0, allow_restart=True)


def test_kill_game_wait_ignores_processes_with_similar_names():
    mocked_config = Mock(
        simulator=False,
        game_process_name="LimbusCompany.exe",
    )
    mocked_screen = Mock()
    mocked_screen.handle.hwnd = 100
    unrelated_process = Mock(info={"name": "NotLimbusCompany.exe"})

    with (
        patch.object(retry_module, "cfg", mocked_config),
        patch.object(retry_module.platform, "system", return_value="Windows"),
        patch.object(
            retry_module.win32process,
            "GetWindowThreadProcessId",
            return_value=(0, 123),
        ),
        patch.object(retry_module, "screen", mocked_screen),
        patch.object(retry_module.subprocess, "run"),
        patch.object(retry_module.psutil, "process_iter", return_value=[unrelated_process]),
        patch.object(retry_module.time, "time", side_effect=[0.0, 0.0]),
        patch.object(retry_module, "sleep") as sleep,
    ):
        retry_module.kill_game()

    sleep.assert_called_once_with(10)


def test_kill_game_wait_accepts_case_insensitive_exact_name():
    mocked_config = Mock(
        simulator=False,
        game_process_name="LimbusCompany.exe",
    )
    mocked_screen = Mock()
    mocked_screen.handle.hwnd = 100
    target_process = Mock(info={"name": "limbuscompany.EXE"})

    with (
        patch.object(retry_module, "cfg", mocked_config),
        patch.object(retry_module.platform, "system", return_value="Windows"),
        patch.object(
            retry_module.win32process,
            "GetWindowThreadProcessId",
            return_value=(0, 123),
        ),
        patch.object(retry_module, "screen", mocked_screen),
        patch.object(retry_module.subprocess, "run"),
        patch.object(
            retry_module.psutil,
            "process_iter",
            side_effect=[[target_process], []],
        ),
        patch.object(retry_module.time, "time", return_value=0.0),
        patch.object(retry_module, "sleep") as sleep,
    ):
        retry_module.kill_game()

    assert sleep.call_args_list == [((10,), {}), ((1,), {})]
