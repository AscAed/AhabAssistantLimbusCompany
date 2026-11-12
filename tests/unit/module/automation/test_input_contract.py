from unittest.mock import patch

import pytest
import win32con

from module.automation.input_handlers import AbstractInput
from module.automation.input_handlers.input import (
    MOUSEEVENTF_LEFTDOWN,
    MOUSEEVENTF_LEFTUP,
    MOUSEEVENTF_MOVE,
    MOUSEEVENTF_WHEEL,
    BackgroundInput,
    Input,
    WindowMoveInput,
)
from module.automation.input_handlers.simulator.mumu_control import MumuControl
from module.automation.input_handlers.simulator.simulator_control import SimulatorControl


def _simulator_instance():
    sim = object.__new__(SimulatorControl)
    sim.simulator_device = None
    sim.simulator_control = None
    sim.simulator_max_x = 1080
    sim.simulator_max_y = 1920
    sim.simulator_port = None
    sim.simulator_bluestacks = False
    sim.is_pause = False
    sim.restore_time = None
    return sim


def _mumu_instance():
    mumu = object.__new__(MumuControl)
    mumu.is_pause = False
    mumu.restore_time = None
    mumu.connect_id = 0
    mumu.display_id = 0
    mumu.device = None
    return mumu


@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("mouse_click", (1, 2)),
        ("mouse_click_blank", ()),
        ("mouse_drag", (1, 2)),
        ("mouse_drag_down", (1, 2)),
        ("mouse_drag_link", ([(1, 2), (3, 4)],)),
        ("mouse_scroll", ()),
        ("mouse_to_blank", ()),
        ("key_press", ("enter",)),
        ("input_text", ("hello",)),
    ],
)
def test_abstract_input_raises_for_unimplemented_methods(method_name, args):
    instance = AbstractInput()
    with pytest.raises(InterruptedError):
        getattr(instance, method_name)(*args)


def test_simulator_coordinate_transform():
    sim = _simulator_instance()
    assert sim._scale(100, 200) == (1080 - 200, 100)

    sim.simulator_max_x = 0
    assert sim._scale(100, 200) == (1, 100)


def test_simulator_reconnect_retries_once_then_succeeds():
    sim = _simulator_instance()
    calls = {"count": 0}

    def flaky_operation():
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("device offline")
        return "ok"

    with patch.object(SimulatorControl, "_is_recoverable_connection_error", return_value=True), patch.object(
        SimulatorControl, "reconnect", return_value=True
    ):
        assert sim._call_with_reconnect("test", flaky_operation) == "ok"

    assert calls["count"] == 2


def test_simulator_reconnect_reraises_when_reconnect_disabled():
    sim = _simulator_instance()

    def failing_operation():
        raise RuntimeError("device offline")

    with patch.object(SimulatorControl, "_is_recoverable_connection_error", return_value=True), patch.object(
        SimulatorControl, "reconnect", return_value=False
    ):
        with pytest.raises(RuntimeError, match="device offline"):
            sim._call_with_reconnect("test", failing_operation)


def test_simulator_mouse_click_forwards_to_device_shell():
    sim = _simulator_instance()
    shell = []

    class FakeDevice:
        def shell(self, command):
            shell.append(command)

    sim.simulator_device = FakeDevice()

    with patch.object(SimulatorControl, "_call_with_reconnect", side_effect=lambda _action, func: func()):
        assert sim.mouse_click(100, 200, times=2) is True

    assert shell == ["input tap 100 200", "input tap 100 200"]


def test_simulator_scroll_placeholder_returns_true():
    assert _simulator_instance().mouse_scroll(-3) is True


def test_mumu_mouse_click_delegates_to_native_click():
    mumu = _mumu_instance()
    clicks = []

    def fake_click(x, y):
        clicks.append((x, y))

    with patch.object(mumu, "click", side_effect=fake_click), patch.object(mumu, "wait_pause"):
        assert mumu.mouse_click(10, 20, times=2) is True

    assert clicks == [(10, 20), (10, 20)]


def test_mumu_key_press_uses_mapped_key_code():
    mumu = _mumu_instance()

    with patch.object(mumu, "key_down") as mock_down, patch.object(mumu, "key_up") as mock_up, patch(
        "module.automation.input_handlers.simulator.mumu_control.time.sleep"
    ):
        mumu.key_press("enter")

    mock_down.assert_called_once_with(28)
    mock_up.assert_called_once_with(28)


def test_mumu_scroll_placeholder_returns_true():
    assert _mumu_instance().mouse_scroll() is True


@patch("module.automation.input_handlers.input.pyautogui")
@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_input_without_driver_uses_pyautogui(mock_cfg, mock_screen, mock_pyautogui):
    mock_cfg.config.use_post_message = True
    mock_screen.handle.rect.return_value = (0, 0, 1920, 1080)
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isMinimized = False

    handler = object.__new__(Input)
    handler.driver = None
    handler.is_pause = False
    handler.restore_time = None
    handler.use_post_message = True

    with patch.object(handler, "pos_offset", side_effect=lambda x, y: (x, y)), patch.object(
        handler, "mouse_move"
    ), patch.object(handler, "get_mouse_position", return_value=(0, 0)), patch.object(
        handler, "wait_pause"
    ), patch("module.automation.input_handlers.input.sleep"), patch(
        "module.automation.input_handlers.input.humanised_delay", return_value=0.0
    ):
        assert handler.mouse_click(10, 20, times=1) is True

    assert mock_pyautogui.mouseDown.called
    assert mock_pyautogui.mouseUp.called


def _lease_handler(mock_screen):
    mock_screen.handle.hwnd = 1000
    mock_screen.handle.isMinimized = False
    handler = object.__new__(WindowMoveInput)
    handler.driver = None
    handler.use_post_message = False
    handler.is_pause = False
    handler.restore_time = None
    return handler


def test_input_class_is_win_abstract_input():
    assert issubclass(Input, AbstractInput)
    assert issubclass(BackgroundInput, AbstractInput)
    assert issubclass(WindowMoveInput, AbstractInput)
    assert issubclass(SimulatorControl, AbstractInput)
    assert issubclass(MumuControl, AbstractInput)


@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_window_move_scroll_uses_focus_lease_and_send_input(mock_cfg, mock_screen):
    mock_cfg.config.mouse_down_duration = 0
    handler = _lease_handler(mock_screen)
    with patch.object(handler, "_wait_for_user_idle", return_value=True), \
        patch.object(handler, "_activate_for_lease", return_value=True), \
        patch.object(handler, "_set_window_pos", return_value=(10, 20)) as move_window, \
        patch.object(handler, "_restore_window_position", return_value=True) as restore_window, \
        patch.object(handler, "_send_mouse_input", return_value=True) as send_input, \
        patch("module.automation.input_handlers.input.win32gui.GetForegroundWindow", return_value=2000), \
        patch("module.automation.input_handlers.input.win32gui.IsWindow", return_value=True), \
        patch("module.automation.input_handlers.input.win32gui.SetForegroundWindow"):
        assert handler.mouse_scroll(direction=-1, x=300, y=400) is True

    move_window.assert_called_once_with(300, 400)
    assert [call.args for call in send_input.call_args_list] == [
        (MOUSEEVENTF_MOVE,),
        (MOUSEEVENTF_WHEEL, -120),
    ]
    restore_window.assert_called_once_with((10, 20))


@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_window_move_scroll_reports_send_input_failure(mock_cfg, mock_screen):
    handler = _lease_handler(mock_screen)
    with patch.object(handler, "_wait_for_user_idle", return_value=True), \
        patch.object(handler, "_activate_for_lease", return_value=True), \
        patch.object(handler, "_set_window_pos", return_value=(10, 20)), \
        patch.object(handler, "_restore_window_position", return_value=True) as restore_window, \
        patch.object(handler, "_send_mouse_input", return_value=False), \
        patch("module.automation.input_handlers.input.win32gui.GetForegroundWindow", return_value=2000), \
        patch("module.automation.input_handlers.input.win32gui.IsWindow", return_value=True), \
        patch("module.automation.input_handlers.input.win32gui.SetForegroundWindow"):
        assert handler.mouse_scroll(direction=1, x=300, y=400) is False

    restore_window.assert_called_once_with((10, 20))


@patch("module.automation.input_handlers.input.pyautogui")
def test_foreground_mouse_move_is_single_low_latency_move(mock_pyautogui):
    handler = object.__new__(Input)
    handler.driver = None
    handler.is_pause = False
    handler.restore_time = None

    with patch.object(handler, "wait_pause"), patch.object(
        handler, "get_mouse_position", return_value=(0, 0)
    ), patch("module.automation.input_handlers.input.sleep") as sleep:
        handler.mouse_move((1600, 900))

    mock_pyautogui.moveTo.assert_called_once_with(1600, 900)
    sleep.assert_not_called()


@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_window_move_click_uses_send_input_without_cursor_motion(mock_cfg, mock_screen):
    mock_cfg.config.mouse_down_duration = 0
    handler = _lease_handler(mock_screen)
    with patch.object(handler, "_wait_for_user_idle", return_value=True), \
        patch.object(handler, "_activate_for_lease", return_value=True), \
        patch.object(handler, "_set_window_pos", return_value=(10, 20)), \
        patch.object(handler, "_restore_window_position", return_value=True) as restore_window, \
        patch.object(handler, "_send_mouse_input", return_value=True) as send_input, \
        patch("module.automation.input_handlers.input.win32api.SetCursorPos") as set_cursor, \
        patch("module.automation.input_handlers.input.pyautogui.moveTo") as move_to, \
        patch("module.automation.input_handlers.input.win32gui.GetForegroundWindow", return_value=2000), \
        patch("module.automation.input_handlers.input.win32gui.IsWindow", return_value=True), \
        patch("module.automation.input_handlers.input.win32gui.SetForegroundWindow"):
        assert handler.mouse_click(300, 400) is True

    assert [call.args[0] for call in send_input.call_args_list] == [
        MOUSEEVENTF_MOVE,
        MOUSEEVENTF_LEFTDOWN,
        MOUSEEVENTF_LEFTUP,
    ]
    set_cursor.assert_not_called()
    move_to.assert_not_called()
    restore_window.assert_called_once_with((10, 20))


@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_window_move_click_wait_timeout_does_not_activate_or_send(mock_cfg, mock_screen):
    handler = _lease_handler(mock_screen)
    with patch.object(handler, "_wait_for_user_idle", return_value=False), \
        patch.object(handler, "_activate_for_lease") as activate, \
        patch.object(handler, "_send_mouse_input") as send_input:
        assert handler.mouse_click(300, 400) is False

    activate.assert_not_called()
    send_input.assert_not_called()


@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_window_move_drag_refreshes_hit_target_before_and_after_window_move(mock_cfg, mock_screen):
    mock_cfg.config.mouse_down_duration = 0
    handler = _lease_handler(mock_screen)
    with patch.object(handler, "_wait_for_user_idle", return_value=True), \
        patch.object(handler, "_activate_for_lease", return_value=True), \
        patch.object(handler, "_set_window_pos", return_value=(10, 20)), \
        patch.object(handler, "_window_move_to", return_value=(10, 20)) as move_window, \
        patch.object(handler, "_restore_window_position", return_value=True), \
        patch.object(handler, "_send_mouse_input", return_value=True) as send_input, \
        patch.object(handler, "_randomize_coords", side_effect=lambda x, y: (x, y)), \
        patch("module.automation.input_handlers.input.win32gui.GetForegroundWindow", return_value=2000), \
        patch("module.automation.input_handlers.input.win32gui.IsWindow", return_value=True), \
        patch("module.automation.input_handlers.input.win32gui.SetForegroundWindow"), \
        patch("module.automation.input_handlers.input.sleep"):
        assert handler.mouse_drag(300, 400, drag_time=0, dx=20, dy=30) is True

    move_window.assert_called_once_with(320, 430, duration=0)
    assert [call.args[0] for call in send_input.call_args_list] == [
        MOUSEEVENTF_MOVE,
        MOUSEEVENTF_LEFTDOWN,
        MOUSEEVENTF_MOVE,
        MOUSEEVENTF_LEFTUP,
    ]


@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_window_move_rejects_physical_input_driver(mock_cfg, mock_screen):
    mock_cfg.config.use_post_message = False
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.rect.return_value = (0, 0, 1920, 1080)
    mock_screen.handle.isMinimized = False

    handler = object.__new__(WindowMoveInput)
    handler.driver = object()
    with patch.object(handler, "get_mouse_position", return_value=(960, 540)):
        with pytest.raises(RuntimeError, match="物理输入驱动"):
            handler._set_window_pos(100, 100)


@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_window_move_rejects_invalid_window_handle(mock_cfg, mock_screen):
    mock_screen.handle.hwnd = 12345
    mock_screen.handle.isMinimized = False
    mock_screen.handle.rect.return_value = (0, 0, 1920, 1080)
    handler = object.__new__(WindowMoveInput)
    handler.driver = None
    with patch.object(handler, "get_mouse_position", return_value=(960, 540)), \
        patch("module.automation.input_handlers.input.win32gui.IsWindow", return_value=False):
        with pytest.raises(RuntimeError, match="句柄无效"):
            handler._set_window_pos(100, 100)


@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_window_move_click_restores_position_after_send_input_failure(mock_cfg, mock_screen):
    handler = _lease_handler(mock_screen)
    with patch.object(handler, "_wait_for_user_idle", return_value=True), \
        patch.object(handler, "_activate_for_lease", return_value=True), \
        patch.object(handler, "_set_window_pos", return_value=(10, 20)), \
        patch.object(handler, "_restore_window_position", return_value=True) as restore_window, \
        patch.object(handler, "_send_mouse_input", side_effect=[False]), \
        patch("module.automation.input_handlers.input.win32gui.GetForegroundWindow", return_value=2000), \
        patch("module.automation.input_handlers.input.win32gui.IsWindow", return_value=True), \
        patch("module.automation.input_handlers.input.win32gui.SetForegroundWindow"):
        assert handler.mouse_click(100, 200) is False

    restore_window.assert_called_once_with((10, 20))


@patch("module.automation.input_handlers.input.screen")
@patch("module.automation.input_handlers.input.cfg")
def test_window_move_lease_restore_failure_is_reported(mock_cfg, mock_screen):
    handler = _lease_handler(mock_screen)
    with patch.object(handler, "_wait_for_user_idle", return_value=True), \
        patch.object(handler, "_activate_for_lease", return_value=True), \
        patch.object(handler, "_set_window_pos", return_value=(10, 20)), \
        patch.object(handler, "_send_mouse_input", return_value=True), \
        patch.object(handler, "_restore_window_position", return_value=False), \
        patch("module.automation.input_handlers.input.win32gui.GetForegroundWindow", return_value=2000), \
        patch("module.automation.input_handlers.input.win32gui.IsWindow", return_value=True), \
        patch("module.automation.input_handlers.input.win32gui.SetForegroundWindow"):
        with pytest.raises(RuntimeError, match="租约释放失败"):
            handler.mouse_click(100, 200)


@patch("module.automation.input_handlers.input.screen")
def test_window_move_restore_failure_does_not_mask_operation_error(mock_screen):
    handler = _lease_handler(mock_screen)
    lease = object()
    with patch.object(handler, "_begin_mouse_lease", return_value=lease), \
        patch.object(handler, "_end_mouse_lease", return_value=False):
        with pytest.raises(ValueError, match="input failed"):
            with handler._mouse_lease(10, 20):
                raise ValueError("input failed")


@patch("module.automation.input_handlers.input.win32gui.IsWindow", return_value=False)
def test_window_move_restore_rejects_destroyed_foreground(mock_is_window):
    handler = object.__new__(WindowMoveInput)
    assert handler._restore_foreground(1234) is False
    mock_is_window.assert_called_once_with(1234)


@patch("module.automation.input_handlers.input.screen")
def test_window_move_restore_position_is_non_activating(mock_screen):
    mock_screen.handle.hwnd = 1000
    mock_screen.handle.rect.return_value = (10, 20, 1930, 1100)
    handler = object.__new__(WindowMoveInput)
    with patch("module.automation.input_handlers.input.win32gui.IsWindow", return_value=True), \
        patch("module.automation.input_handlers.input.win32gui.SetWindowPos") as set_pos:
        assert handler._restore_window_position((10, 20)) is True

    flags = set_pos.call_args.args[-1]
    assert flags & win32con.SWP_NOACTIVATE
    assert flags & win32con.SWP_NOZORDER


def test_window_move_activation_verifies_target_foreground():
    handler = object.__new__(WindowMoveInput)
    with patch("module.automation.input_handlers.input.win32gui.SetForegroundWindow") as activate, \
        patch("module.automation.input_handlers.input.win32gui.GetForegroundWindow", return_value=1000):
        assert handler._activate_for_lease(1000) is True

    activate.assert_called_once_with(1000)


@patch("module.automation.input_handlers.input.screen")
def test_window_move_lease_restores_original_foreground_after_input(mock_screen):
    handler = _lease_handler(mock_screen)
    lease = type("Lease", (), {
        "game_hwnd": 1000,
        "original_foreground": 2000,
        "original_position": (10, 20),
        "original_cursor": (500, 400),
        "was_paused": False,
    })()
    with patch.object(handler, "_restore_window_position", return_value=True) as restore_position, \
        patch.object(handler, "_restore_foreground", return_value=True) as restore_foreground:
        assert handler._end_mouse_lease(lease) is True

    restore_position.assert_called_once_with((10, 20))
    restore_foreground.assert_called_once_with(2000)
