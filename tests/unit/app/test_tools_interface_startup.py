import os
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.tools_interface import ToolsInterface
from tasks.tools import ToolManager


class _StartupLoopExceeded(BaseException):
    pass


def test_tool_start_returns_after_startup_deadline_and_cancels_pending_window():
    tool = SimpleNamespace(
        initialized=False,
        w=None,
        cancel_startup=Mock(),
    )
    interface = SimpleNamespace(tools={})
    process_events = Mock(side_effect=[None, None, _StartupLoopExceeded()])

    with patch("app.tools_interface.tools.start", return_value=tool), patch(
        "app.tools_interface.QApplication.processEvents", process_events
    ), patch("time.monotonic", side_effect=[0, 1, 2, 10]), patch(
        "app.tools_interface.sleep"
    ):
        assert ToolsInterface._tool_start(interface, "battle", object()) is False

    process_events.assert_has_calls([call(), call()])
    tool.cancel_startup.assert_called_once()
    assert interface.tools == {}


def test_cancelled_startup_does_not_create_a_tool_window():
    manager = ToolManager("battle")
    manager.cancel_startup()

    with patch(
        "tasks.tools.QApplication.instance", return_value=object()
    ), patch(
        "tasks.tools.QTimer.singleShot",
        side_effect=lambda _delay, _app, callback: callback(),
    ), patch("tasks.tools.InfiniteBattles") as battle_window:
        manager.run_tools()

    battle_window.assert_not_called()
    assert manager.initialized is None
