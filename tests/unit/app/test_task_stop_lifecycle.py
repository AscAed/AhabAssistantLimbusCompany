import os
from types import MethodType, SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from app.farming_interface import FarmingInterfaceLeft
from app.my_app import MainWindow
from module.my_error.my_error import userStopError, withOutGameWinError
from tasks.base import script_task_scheme
from tasks.tools.infinite_battle import BattleWorker, InfiniteBattles
from tasks.tools.production_module import ProductionModule, ProductionWork


class _Signal:
    def __init__(self):
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)

    def emit(self):
        for callback in list(self.callbacks):
            callback()


class _Worker:
    def __init__(self, finish_on_wait=False):
        self.running = True
        self.is_stop = False
        self.finish_on_wait = finish_on_wait
        self.finished = _Signal()
        self.terminate = Mock()

    def isRunning(self):
        return self.running

    def wait(self, _timeout):
        if self.finish_on_wait:
            self.running = False
        return not self.running

    def stop(self):
        self.is_stop = True


def _farming_left(worker):
    button = SimpleNamespace(
        get_text=lambda: "S t o p !",
        set_text=Mock(),
        button=Mock(),
    )
    left = SimpleNamespace(
        my_script=worker,
        link_start_button=button,
        parent=lambda: None,
        tr=lambda text: text,
        _enable_setting=Mock(),
        reset_pause_resume_button=Mock(),
    )
    for name in ("stop_script", "_on_script_finished", "_finish_manual_stop_cleanup"):
        if hasattr(FarmingInterfaceLeft, name):
            setattr(left, name, MethodType(getattr(FarmingInterfaceLeft, name), left))
    return left


def test_init_game_stops_when_worker_flag_is_set_before_window_found():
    worker = SimpleNamespace(is_stop=True)
    with patch.object(script_task_scheme, "cfg") as cfg, patch.object(
        script_task_scheme.game_process, "start_game"
    ) as start_game, patch.object(script_task_scheme.auto, "init_input"):
        cfg.simulator = False
        with pytest.raises(userStopError):
            script_task_scheme.init_game(thread=worker)

    start_game.assert_not_called()


def test_init_game_window_discovery_has_deadline():
    with patch.object(script_task_scheme, "cfg") as cfg, patch.object(
        script_task_scheme.game_process, "start_game"
    ), patch.object(script_task_scheme.auto, "init_input"), patch.object(
        script_task_scheme.screen, "init_handle", return_value=False
    ) as find_window, patch.object(
        script_task_scheme, "monotonic", side_effect=[0, 1, 121]
    ), patch.object(script_task_scheme, "sleep"):
        cfg.simulator = False
        with pytest.raises(withOutGameWinError):
            script_task_scheme.init_game(thread=SimpleNamespace(is_stop=False))

    assert find_window.call_count == 2


def test_script_task_initial_capture_observes_worker_stop():
    worker = SimpleNamespace(is_stop=False)

    def capture(*_args, **kwargs):
        worker.is_stop = True
        assert kwargs["stop_check"]() is True
        raise userStopError("stop during initial capture")

    with patch.object(script_task_scheme, "init_game"), patch.object(
        script_task_scheme, "cfg"
    ) as cfg, patch.object(script_task_scheme, "path_manager"), patch.object(
        script_task_scheme, "auto"
    ) as auto:
        cfg.simulator = True
        cfg.skip_enkephalin = False
        cfg.resonate_with_Ahab = False
        auto.take_screenshot.side_effect = capture
        auto.click_element.side_effect = AssertionError("initial capture missed stop check")

        with pytest.raises(userStopError):
            script_task_scheme.script_task(thread=worker)


def test_script_task_initial_battle_observes_worker_stop():
    from PIL import Image

    from module.automation.automation import Automation

    worker = SimpleNamespace(is_stop=False)
    automation = object.__new__(Automation)
    automation.model = "clam"
    automation.screenshot = None
    automation.screenshot_np = None
    automation.last_screenshot_time = 0
    automation.init_input = Mock()
    automation.clear_img_cache = Mock()
    automation.click_element = Mock(return_value=True)
    frame = Image.new("L", (4, 4), color=0)

    def stop_then_capture_again(*_args, **_kwargs):
        worker.is_stop = True
        automation.take_screenshot()

    with patch.object(script_task_scheme, "init_game"), patch.object(
        script_task_scheme, "auto", automation
    ), patch.object(
        script_task_scheme, "path_manager"
    ), patch.object(
        script_task_scheme.battle, "fight", side_effect=stop_then_capture_again
    ), patch(
        "module.automation.automation.cfg"
    ) as auto_cfg, patch(
        "module.automation.automation.ScreenShot.take_screenshot", return_value=frame
    ), patch("module.automation.automation.time.sleep"), patch.object(
        script_task_scheme, "cfg"
    ) as cfg:
        auto_cfg.operation_mode = "foreground_mouse"
        auto_cfg.screenshot_interval = 0.1
        cfg.simulator = True
        cfg.skip_enkephalin = False
        cfg.resonate_with_Ahab = False
        cfg.daily_task = False
        cfg.get_reward = False
        cfg.buy_enkephalin = False
        cfg.mirror = False
        cfg.set_reduce_miscontact = False

        with pytest.raises(userStopError):
            script_task_scheme.script_task(thread=worker)


def test_completion_exit_requests_cooperative_window_close():
    window = SimpleNamespace(close=Mock())
    left = SimpleNamespace(
        after_completion_selector=SimpleNamespace(_hide_editor=Mock()),
        window=lambda: window,
    )
    with patch("app.farming_interface.sys.exit") as exit_process:
        FarmingInterfaceLeft.stop_AALC(left)

    window.close.assert_called_once()
    assert window._close_confirmed is True
    exit_process.assert_not_called()


def test_battle_worker_does_not_start_actions_after_stop_during_initialization():
    worker = BattleWorker()
    worker.battle.fight = Mock()
    with patch.object(
        script_task_scheme, "init_game", side_effect=lambda **_kwargs: worker.stop()
    ), patch.object(worker, "_set_win") as set_window, patch(
        "tasks.tools.infinite_battle.path_manager"
    ), patch("tasks.tools.infinite_battle.auto"):
        worker.run()

    set_window.assert_not_called()
    worker.battle.fight.assert_not_called()


def test_battle_worker_reports_runtime_failure_from_fight():
    worker = BattleWorker()
    worker.initialized = True
    worker.battle.fight = Mock(side_effect=RuntimeError("等待截图超时"))
    errors = []
    worker.error_occurred.connect(errors.append)

    worker._run_battle_worker()

    assert errors == ["战斗执行错误: 等待截图超时"]


def test_production_worker_does_not_start_actions_after_stop_during_initialization():
    worker = ProductionWork()
    worker._back_init_menu_with_tool_policy = Mock(side_effect=AssertionError("action after stop"))
    with patch.object(
        script_task_scheme, "init_game", side_effect=lambda **_kwargs: worker.stop()
    ), patch.object(worker, "_set_win") as set_window:
        worker.run()

    set_window.assert_not_called()
    worker._back_init_menu_with_tool_policy.assert_not_called()


def test_production_worker_stop_interrupts_nested_screenshot_before_input():
    from PIL import Image

    from module.automation.automation import Automation

    worker = ProductionWork()
    worker._set_win = Mock()
    worker._back_init_menu_with_tool_policy = Mock(return_value=True)
    automation = object.__new__(Automation)
    automation.screenshot = None
    automation.screenshot_np = None
    automation.last_screenshot_time = 0
    automation.find_element = Mock(return_value=True)
    automation.mouse_click = Mock()

    def stop_during_capture(_gray):
        worker.stop()
        return Image.new("L", (4, 4), color=0)

    def nested_enkephalin_capture(*_args, **_kwargs):
        automation.take_screenshot()
        automation.mouse_click(100, 100)

    with patch.object(script_task_scheme, "init_game"), patch(
        "tasks.tools.production_module.auto", automation
    ), patch(
        "tasks.tools.production_module.make_enkephalin_module",
        side_effect=nested_enkephalin_capture,
    ), patch(
        "tasks.tools.production_module.get_current_enkephalin", return_value=None
    ) as get_enkephalin, patch.object(
        automation, "mouse_click"
    ) as mouse_click, patch(
        "module.automation.automation.cfg"
    ) as mock_cfg, patch(
        "module.automation.automation.ScreenShot.take_screenshot",
        side_effect=stop_during_capture,
    ), patch("module.automation.automation.time.sleep"):
        mock_cfg.operation_mode = "foreground_mouse"
        mock_cfg.screenshot_interval = 0.1
        worker.run()

    assert worker.is_stop is True
    mouse_click.assert_not_called()
    get_enkephalin.assert_not_called()


def test_manual_stop_requests_task_stop_before_simulator_cleanup():
    worker = _Worker(finish_on_wait=True)
    left = _farming_left(worker)
    stopped_at_cleanup = []
    with patch("app.farming_interface.cfg") as cfg, patch(
        "module.automation.input_handlers.simulator.mumu_control.MumuControl.clean_connect",
        side_effect=lambda: stopped_at_cleanup.append(worker.is_stop),
    ), patch("app.farming_interface.auto"), patch("app.farming_interface.mediator"):
        cfg.simulator = True
        cfg.simulator_type = 0
        cfg.set_reduce_miscontact = False

        FarmingInterfaceLeft.start_and_stop_tasks(left)

    assert stopped_at_cleanup == [True]
    worker.terminate.assert_not_called()


def test_manual_stop_keeps_start_disabled_while_worker_runs():
    worker = _Worker()
    left = _farming_left(worker)
    with patch("app.farming_interface.cfg") as cfg, patch(
        "app.farming_interface.auto"
    ), patch("app.farming_interface.mediator"), patch(
        "module.automation.input_handlers.simulator.mumu_control.MumuControl.clean_connect"
    ) as clean_connect:
        cfg.simulator = True
        cfg.simulator_type = 0
        cfg.set_reduce_miscontact = False

        FarmingInterfaceLeft.start_and_stop_tasks(left)

    assert worker.is_stop is True
    assert left.link_start_button.set_text.call_args.args[0] != "Link Start!"
    left.link_start_button.button.setEnabled.assert_called_with(False)
    left._enable_setting.assert_not_called()
    clean_connect.assert_not_called()


def test_stop_script_keeps_stop_request_when_pause_inspection_fails():
    worker = _Worker()
    left = _farming_left(worker)
    with patch(
        "app.farming_interface.auto.check_pause", side_effect=RuntimeError("pause unavailable")
    ):
        assert left.stop_script(timeout_ms=0) is False

    assert worker.is_stop is True
    left.link_start_button.button.setEnabled.assert_called_with(False)


def test_main_window_close_defers_until_task_worker_finishes():
    worker = _Worker()
    left = _farming_left(worker)
    window = SimpleNamespace(
        farming_interface=SimpleNamespace(interface_left=left),
        tools_interface=SimpleNamespace(tools={}),
        x=lambda: 0,
        y=lambda: 0,
        isVisible=lambda: True,
        tr=lambda text: text,
        window=lambda: None,
        close=Mock(),
    )
    event = Mock()
    with patch("app.my_app.cfg"), patch(
        "app.my_app.MessageBoxConfirm"
    ) as confirm, patch("app.farming_interface.auto"):
        confirm.return_value.exec.return_value = True
        MainWindow.closeEvent(window, event)

    assert worker.is_stop is True
    event.ignore.assert_called_once()
    worker.terminate.assert_not_called()
    window.close.assert_not_called()
    worker.running = False
    worker.finished.emit()
    window.close.assert_called_once()


@pytest.mark.parametrize("window_class", [InfiniteBattles, ProductionModule])
def test_tool_window_close_does_not_force_terminate_worker(window_class):
    worker = _Worker()
    window = SimpleNamespace(worker=worker, close=Mock(), listener=Mock())
    event = Mock()

    with patch("tasks.tools.infinite_battle.screen"), patch(
        "tasks.tools.infinite_battle.auto"
    ), patch("tasks.tools.production_module.screen"), patch(
        "tasks.tools.production_module.auto"
    ):
        window_class.closeEvent(window, event)

    assert worker.is_stop is True
    event.ignore.assert_called_once()
    event.accept.assert_not_called()
    worker.terminate.assert_not_called()
    worker.running = False
    worker.finished.emit()
    window.close.assert_called_once()
