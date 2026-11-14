import os
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from app.my_app import MainWindow
from app.resource_sync_coordinator import ResourceSyncCoordinator
from app.startup_options import (
    SKIP_STARTUP_NETWORK_CHECKS_ARG,
    filter_startup_network_checks_arg,
    has_skip_startup_network_checks,
)


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _make_coordinator(qapp, *, skip_startup_network_checks: bool):
    window = QWidget()
    continuation = Mock()
    coordinator = ResourceSyncCoordinator(
        window=window,
        status_label=QLabel(window),
        startup_argv=["AALC.exe"],
        continue_startup=continuation,
        set_progress=Mock(),
        has_running_script=Mock(return_value=False),
        skip_startup_network_checks=skip_startup_network_checks,
        service=Mock(),
    )
    return coordinator, continuation


def test_startup_network_flag_is_detected_and_removed_from_qt_args():
    argv = ["AALC.exe", SKIP_STARTUP_NETWORK_CHECKS_ARG, "start"]

    assert has_skip_startup_network_checks(argv)
    assert filter_startup_network_checks_arg(argv) == ["AALC.exe", "start"]
    assert not has_skip_startup_network_checks(["AALC.exe", "start"])


def test_skip_startup_checks_defers_continuation_without_starting_remote_work(
    qapp, monkeypatch
):
    coordinator, continuation = _make_coordinator(
        qapp, skip_startup_network_checks=True
    )
    scheduled = []
    timer_stub = SimpleNamespace(
        singleShot=lambda delay, callback: scheduled.append((delay, callback))
    )
    monkeypatch.setattr("app.resource_sync_coordinator.QTimer", timer_stub)
    check_update = Mock(side_effect=AssertionError("remote version check started"))
    start_worker = Mock(side_effect=AssertionError("resource worker started"))
    monkeypatch.setattr("app.resource_sync_coordinator.check_update", check_update)
    monkeypatch.setattr(coordinator, "_start_resource_sync_worker", start_worker)

    coordinator.start_startup_check()

    assert len(scheduled) == 1
    assert scheduled[0][0] == 0
    check_update.assert_not_called()
    start_worker.assert_not_called()

    scheduled[0][1]()
    scheduled[0][1]()
    continuation.assert_called_once_with()


def test_default_startup_still_runs_existing_version_gate(qapp, monkeypatch):
    coordinator, _ = _make_coordinator(qapp, skip_startup_network_checks=False)
    start_gate = Mock()
    monkeypatch.setattr(coordinator, "_start_resource_sync_gate_check", start_gate)

    coordinator.start_startup_check()

    start_gate.assert_called_once_with(trigger="startup")


def test_startup_continuation_skips_only_announcement_in_opt_out_mode():
    window = SimpleNamespace(
        _skip_startup_network_checks=True,
        show_announcement_board=Mock(),
        command_start=Mock(),
        init_system_tray=Mock(),
    )
    argv = ["AALC.exe", SKIP_STARTUP_NETWORK_CHECKS_ARG, "start"]

    MainWindow._continue_main_startup_sequence(window, argv)

    window.show_announcement_board.assert_not_called()
    window.command_start.assert_called_once_with(["AALC.exe", "start"])
    window.init_system_tray.assert_called_once_with()


def test_startup_continuation_keeps_announcement_by_default():
    window = SimpleNamespace(
        _skip_startup_network_checks=False,
        show_announcement_board=Mock(),
        command_start=Mock(),
        init_system_tray=Mock(),
    )
    argv = ["AALC.exe", "start"]

    MainWindow._continue_main_startup_sequence(window, argv)

    window.show_announcement_board.assert_called_once_with()
    window.command_start.assert_called_once_with(argv)
    window.init_system_tray.assert_called_once_with()
