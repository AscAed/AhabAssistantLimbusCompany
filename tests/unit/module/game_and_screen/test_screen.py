import threading
from unittest.mock import Mock, patch

import win32con

from module.game_and_screen.screen import Handle, Screen, WindowVisibilitySnapshot


def _handle():
    handle = object.__new__(Handle)
    handle._hwnd = 1000
    handle._enum_windows_list = []
    handle._background_input_hidden = False
    handle._transparent = False
    return handle


@patch("module.game_and_screen.screen.win32gui.IsWindow", return_value=True)
@patch("module.game_and_screen.screen.win32gui.SetWindowPos")
@patch("module.game_and_screen.screen.ctypes.windll.user32.SetLayeredWindowAttributes")
@patch("module.game_and_screen.screen.win32gui.SetWindowLong")
@patch("module.game_and_screen.screen.win32gui.GetWindowLong", return_value=0)
def test_hide_for_background_input_sets_layered_without_transparent(
    mock_get_long,
    mock_set_long,
    mock_set_layered,
    mock_set_pos,
    mock_is_window,
):
    handle = _handle()

    snapshot = handle.hide_for_background_input()

    assert snapshot is not None
    assert snapshot.ex_style == 0
    assert mock_get_long.called
    mock_set_long.assert_called_once_with(1000, win32con.GWL_EXSTYLE, win32con.WS_EX_LAYERED)
    mock_set_layered.assert_called_once_with(1000, 0, 0, win32con.LWA_ALPHA)
    flags = mock_set_pos.call_args.args[-1]
    assert flags & win32con.SWP_NOZORDER
    assert flags & win32con.SWP_NOACTIVATE
    assert not (mock_set_long.call_args.args[2] & win32con.WS_EX_TRANSPARENT)
    assert handle.is_background_input_hidden is True
    assert handle.isTransparent is False


@patch("module.game_and_screen.screen.win32gui.IsWindow", return_value=True)
@patch("module.game_and_screen.screen.win32gui.SetWindowPos")
@patch("module.game_and_screen.screen.ctypes.windll.user32.SetLayeredWindowAttributes")
@patch("module.game_and_screen.screen.win32gui.SetWindowLong")
def test_restore_background_input_visibility_restores_snapshot(
    mock_set_long,
    mock_set_layered,
    mock_set_pos,
    mock_is_window,
):
    handle = _handle()
    snapshot = WindowVisibilitySnapshot(
        ex_style=win32con.WS_EX_LAYERED | 0x1234,
        layered_alpha=137,
        layered_flags=3,
        layered_color_key=0,
    )

    assert handle.restore_background_input_visibility(snapshot) is True
    mock_set_long.assert_called_once_with(1000, win32con.GWL_EXSTYLE, snapshot.ex_style)
    mock_set_layered.assert_called_once_with(1000, 0, 137, 3)
    flags = mock_set_pos.call_args.args[-1]
    assert flags & win32con.SWP_NOZORDER
    assert flags & win32con.SWP_NOACTIVATE
    assert handle.is_background_input_hidden is False
    assert handle.isTransparent is True


@patch("module.game_and_screen.screen.win32gui.IsWindow", return_value=True)
@patch("module.game_and_screen.screen.win32gui.SetWindowPos")
@patch("module.game_and_screen.screen.ctypes.windll.user32.SetLayeredWindowAttributes", side_effect=RuntimeError("boom"))
@patch("module.game_and_screen.screen.win32gui.SetWindowLong")
@patch("module.game_and_screen.screen.win32gui.GetWindowLong", return_value=0)
def test_hide_for_background_input_rolls_back_on_failure(
    mock_get_long,
    mock_set_long,
    mock_set_layered,
    mock_set_pos,
    mock_is_window,
):
    handle = _handle()

    assert handle.hide_for_background_input() is None
    assert mock_get_long.called
    assert mock_set_layered.called
    assert mock_set_long.call_count >= 2
    assert handle.is_background_input_hidden is False
    assert handle.isTransparent is False
    mock_set_pos.assert_called_once()


@patch("module.game_and_screen.screen.win32gui.IsWindow", return_value=True)
@patch("module.game_and_screen.screen.win32gui.SetWindowPos")
@patch(
    "module.game_and_screen.screen.ctypes.windll.user32.GetLayeredWindowAttributes",
    return_value=0,
)
@patch("module.game_and_screen.screen.win32gui.SetWindowLong")
@patch(
    "module.game_and_screen.screen.win32gui.GetWindowLong",
    return_value=win32con.WS_EX_LAYERED,
)
def test_hide_for_background_input_refuses_unreadable_layered_state(
    mock_get_long,
    mock_set_long,
    mock_get_layered,
    mock_set_pos,
    mock_is_window,
):
    handle = _handle()

    assert handle.hide_for_background_input() is None

    mock_get_long.assert_called_with(1000, win32con.GWL_EXSTYLE)
    mock_get_layered.assert_called_once()
    mock_set_long.assert_not_called()
    mock_set_pos.assert_not_called()
    assert handle.is_background_input_hidden is False


@patch("module.game_and_screen.screen.win32gui.IsWindow", return_value=True)
@patch("module.game_and_screen.screen.win32gui.SetWindowPos")
@patch(
    "module.game_and_screen.screen.ctypes.windll.user32.SetLayeredWindowAttributes",
    return_value=0,
)
@patch("module.game_and_screen.screen.win32gui.SetWindowLong")
def test_restore_background_input_visibility_reports_native_api_failure(
    mock_set_long,
    mock_set_layered,
    mock_set_pos,
    mock_is_window,
):
    handle = _handle()
    snapshot = WindowVisibilitySnapshot(
        ex_style=win32con.WS_EX_LAYERED,
        layered_alpha=137,
        layered_flags=win32con.LWA_ALPHA,
        layered_color_key=0,
    )

    assert handle.restore_background_input_visibility(snapshot) is False
    mock_set_long.assert_called_once_with(1000, win32con.GWL_EXSTYLE, snapshot.ex_style)
    mock_set_layered.assert_called_once_with(1000, 0, 137, win32con.LWA_ALPHA)
    mock_set_pos.assert_not_called()
    assert handle.is_background_input_hidden is False


def test_snapshot_and_restore_preserve_layered_color_key():
    import ctypes

    handle = _handle()
    color_key = 0x123456

    def read_layered_attributes(_hwnd, color_key_ptr, alpha_ptr, flags_ptr):
        ctypes.cast(color_key_ptr, ctypes.POINTER(ctypes.c_uint)).contents.value = color_key
        ctypes.cast(alpha_ptr, ctypes.POINTER(ctypes.c_ubyte)).contents.value = 137
        ctypes.cast(flags_ptr, ctypes.POINTER(ctypes.c_uint)).contents.value = win32con.LWA_COLORKEY
        return 1

    with patch(
        "module.game_and_screen.screen.win32gui.GetWindowLong",
        return_value=win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT,
    ), patch(
        "module.game_and_screen.screen.ctypes.windll.user32.GetLayeredWindowAttributes",
        side_effect=read_layered_attributes,
    ), patch(
        "module.game_and_screen.screen.win32gui.SetWindowLong"
    ), patch(
        "module.game_and_screen.screen.ctypes.windll.user32.SetLayeredWindowAttributes"
    ) as set_layered, patch(
        "module.game_and_screen.screen.win32gui.SetWindowPos"
    ), patch(
        "module.game_and_screen.screen.win32gui.IsWindow", return_value=True
    ):
        snapshot = handle.snapshot_window_visibility()
        assert snapshot is not None
        assert getattr(snapshot, "layered_color_key", None) == color_key

        assert handle.restore_background_input_visibility(snapshot) is True

    set_layered.assert_called_once_with(
        1000,
        color_key,
        137,
        win32con.LWA_COLORKEY,
    )


@patch("module.game_and_screen.screen.sleep")
@patch("module.game_and_screen.screen.cfg")
def test_set_win_exception_retry_is_bounded(mock_cfg, mock_sleep):
    screen = object.__new__(Screen)
    handle = Mock()
    handle.isMinimized = False
    handle.isActive = True

    calls = 0

    class RetryLimitReached(BaseException):
        pass

    def width_raises(*_args):
        nonlocal calls
        calls += 1
        if calls > 6:
            raise RetryLimitReached("window size retry was unbounded")
        raise RuntimeError("window handle unavailable")

    handle.width.side_effect = width_raises
    screen.handle = handle
    mock_cfg.operation_mode = "background_window"
    mock_cfg.set_win_size = 1440
    mock_cfg.set_win_position = "free"
    mock_cfg.set_windows = False

    errors = []

    def run_set_win():
        try:
            screen.set_win()
        except BaseException as exc:
            errors.append(exc)

    worker = threading.Thread(target=run_set_win, daemon=True)
    worker.start()
    worker.join(timeout=1)

    assert not worker.is_alive(), "set_win must stop retrying after its configured bound"
    assert handle.width.call_count <= 5
    assert len(errors) == 1
    assert isinstance(errors[0], RuntimeError)
    assert "设置窗口失败" in str(errors[0])
