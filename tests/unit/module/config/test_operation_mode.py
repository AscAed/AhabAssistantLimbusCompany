from unittest.mock import patch

import pytest

from module.automation.screenshot import ScreenShot
from module.config.config import migrate_operation_mode


@pytest.mark.parametrize(
    ("loaded", "expected"),
    [
        ({"operation_mode": "foreground_mouse"}, "foreground_mouse"),
        ({"operation_mode": "background_window"}, "background_window"),
        ({"win_input_type": "foreground"}, "foreground_mouse"),
        ({"win_input_type": "background"}, "background_window"),
        ({"win_input_type": "window_move"}, "background_window"),
        ({"background_click": False}, "foreground_mouse"),
        ({"background_click": True}, "background_window"),
        ({}, "background_window"),
    ],
)
def test_migrate_operation_mode(loaded, expected):
    assert migrate_operation_mode(loaded) == expected


@pytest.mark.parametrize("value", [None, "", "unknown", 1, True])
def test_migrate_operation_mode_rejects_invalid_explicit_values(value):
    with pytest.raises(ValueError, match="operation_mode"):
        migrate_operation_mode({"operation_mode": value})


@pytest.mark.parametrize(
    ("mode", "expected_method"),
    [
        ("foreground_mouse", "take_screenshot_gdi"),
        ("background_window", "background_screenshot"),
    ],
)
def test_screenshot_backend_follows_operation_mode(mode, expected_method):
    with patch("module.automation.screenshot.cfg") as mock_cfg, \
        patch("module.automation.screenshot.screen") as mock_screen, \
        patch.object(ScreenShot, "take_screenshot_gdi", return_value="foreground") as gdi, \
        patch.object(ScreenShot, "background_screenshot", return_value="background") as background:
        mock_cfg.simulator = False
        mock_cfg.operation_mode = mode
        mock_screen.handle.bring_window_into_view.return_value = None

        result = ScreenShot.take_screenshot(gray=True)

    assert result == ("foreground" if expected_method == "take_screenshot_gdi" else "background")
    assert getattr(gdi if expected_method == "take_screenshot_gdi" else background, "called")


def test_background_window_scroll_uses_public_default_step():
    import inspect

    from module.automation.input_handlers.input import WindowMoveInput

    assert inspect.signature(WindowMoveInput.mouse_scroll).parameters["direction"].default == -3
