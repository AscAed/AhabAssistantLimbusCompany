import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.my_app import MainWindow


def test_download_failure_hides_progress_before_showing_warning():
    events = []
    window = SimpleNamespace(
        progress_ring=SimpleNamespace(hide=lambda: events.append("hide")),
        hide_download_progress=lambda: events.append("hide"),
        show_warning=lambda message: events.append(("warning", message)),
    )

    MainWindow.handle_download_failed(window, "download failed")

    assert events == ["hide", ("warning", "download failed")]


def test_download_progress_finished_hides_ring():
    events = []
    window = SimpleNamespace(
        progress_ring=SimpleNamespace(hide=lambda: events.append("hide")),
    )

    MainWindow.hide_download_progress(window)

    assert events == ["hide"]


def test_download_completion_hides_progress_before_confirmation(monkeypatch):
    events = []
    window = SimpleNamespace(
        progress_ring=SimpleNamespace(hide=lambda: events.append("hide")),
        hide_download_progress=lambda: events.append("hide"),
        tr=lambda message: message,
        window=lambda: None,
    )

    class ConfirmDialog:
        def __init__(self, title, message, parent):
            events.append("confirm")

        def exec(self):
            return False

    monkeypatch.setattr("app.my_app.MessageBoxConfirm", ConfirmDialog)
    MainWindow.download_and_install(window, "AALC.zip")

    assert events == ["hide", "confirm"]
