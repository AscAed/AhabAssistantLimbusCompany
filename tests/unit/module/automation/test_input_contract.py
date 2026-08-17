from unittest.mock import patch

import pytest

from module.automation.input_handlers import AbstractInput
from module.automation.input_handlers.input import BackgroundInput, Input, WindowMoveInput
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


def test_window_move_scroll_reports_unsupported():
    wm = object.__new__(WindowMoveInput)
    assert wm.mouse_scroll() is False


def test_input_class_is_win_abstract_input():
    assert issubclass(Input, AbstractInput)
    assert issubclass(BackgroundInput, AbstractInput)
    assert issubclass(WindowMoveInput, AbstractInput)
    assert issubclass(SimulatorControl, AbstractInput)
    assert issubclass(MumuControl, AbstractInput)
